"""
Module containing functions for running value network tuning with self-tuning approach
"""

import os.path
from collections import defaultdict
from pathlib import Path
from random import shuffle

import torch
from CGRtools.containers import MoleculeContainer
from pytorch_lightning import Trainer
from pytorch_lightning.callbacks import LearningRateMonitor
from torch.utils.data import random_split
from torch_geometric.data.lightning import LightningDataset
from tqdm import tqdm

from SynTool.mcts.tree import Tree
from SynTool.utils.files import MoleculeReader
from SynTool.ml.training.preprocessing import ValueNetworkDataset
from SynTool.chem.retron import compose_retrons
from SynTool.utils.logging import DisableLogger, HiddenPrints
from SynTool.ml.networks.value import ValueNetwork
from SynTool.utils.loading import load_value_net
from SynTool.mcts.expansion import PolicyFunction
from SynTool.mcts.evaluation import ValueFunction
from SynTool.utils.config import TreeConfig, PolicyNetworkConfig, ValueNetworkConfig, ReinforcementConfig


def create_value_network(value_config):

    weights_path = Path(value_config.weights_path)
    value_network = ValueNetwork(vector_dim=value_config.vector_dim,
                                 batch_size=value_config.batch_size,
                                 dropout=value_config.dropout,
                                 num_conv_layers=value_config.num_conv_layers,
                                 learning_rate=value_config.learning_rate)

    with DisableLogger() as DL, HiddenPrints() as HP:
        trainer = Trainer()
        trainer.strategy.connect(value_network)
        trainer.save_checkpoint(weights_path)

    return value_network



def create_targets_batch(targets, batch_size):

    num_targets = len(targets)
    batch_splits = list(range(num_targets // batch_size + int(bool(num_targets % batch_size))))

    if int(num_targets / batch_size) == 0:
        print(f'1 batch were created with {num_targets} molecules')
    else:
        print(f'{len(batch_splits)} batches were created with {batch_size} molecules each')

    targets_batch_list = []
    for batch_id in batch_splits:
        batch_slices = [i for i in range(batch_id * batch_size, (batch_id + 1) * batch_size) if i < len(targets)]
        targets_batch_list.append([targets[i] for i in batch_slices])

    return targets_batch_list



def extract_tree_retrons(tree_list):
    """
    Takes a built tree and a dictionary of processed molecules extracted from the previous trees as input, and returns
    the updated dictionary of processed molecules after adding the solved nodes from the given tree.

    :param tree_list: The built tree
    """
    extracted_retrons = defaultdict(float)
    for tree in tree_list:
        for idx, node in tree.nodes.items():
            # add solved nodes to set
            if node.is_solved():
                parent = idx
                while parent and parent != 1:
                    composed_smi = str(compose_retrons(tree.nodes[parent].new_retrons))
                    extracted_retrons[composed_smi] = 1.0
                    parent = tree.parents[parent]
            else:
                composed_smi = str(compose_retrons(tree.nodes[idx].new_retrons))
                extracted_retrons[composed_smi] = 0.0

    # shuffle extracted retrons
    processed_keys = list(extracted_retrons.keys())
    shuffle(processed_keys)
    extracted_retrons = {i: extracted_retrons[i] for i in processed_keys}

    return extracted_retrons


def run_tree_search(target: MoleculeContainer,
                    tree_config: TreeConfig,
                    policy_config: PolicyNetworkConfig,
                    value_config: ValueNetworkConfig,
                    reaction_rules_path: str,
                    building_blocks_path: str):
    """
    Takes a target molecule and a planning configuration dictionary as input, preprocesses the target molecule,
    initializes a tree and then runs the tree search algorithm.

    :param target: The target molecule. It can be either a `MoleculeContainer` object or a SMILES string
    :param tree_config: The planning configuration that contains settings for tree search
    :return: The built tree
    """

    # policy and value function loading
    # TODO solve this problem between network and policy config
    policy_function = PolicyFunction(policy_config=policy_config)
    value_function = ValueFunction(weights_path=value_config.weights_path)

    # initialize tree
    tree_config.silent = True
    tree = Tree(target=target,
                tree_config=tree_config,
                reaction_rules_path=reaction_rules_path,
                building_blocks_path=building_blocks_path,
                policy_function=policy_function,
                value_function=value_function
                )

    # remove target from buildings blocs
    if str(target) in tree.building_blocks:
        tree.building_blocks.remove(str(target))

    # run tree search
    _ = list(tree)

    return tree


def create_tuning_set(extracted_retrons, batch_size=1):
    """
    Creates a tuning dataset from a given processed molecules extracted from the trees from the
    planning stage and returns a LightningDataset object with a specified batch size for tuning value neural network.

    :param batch_size:
    :param extracted_retrons: The path to the directory where the processed molecules is stored
    :return: A LightningDataset object, which contains the tuning sets for value network tuning
    """

    full_dataset = ValueNetworkDataset(extracted_retrons)
    train_size = int(0.6 * len(full_dataset))
    val_size = len(full_dataset) - train_size

    train_set, val_set = random_split(full_dataset, [train_size, val_size], torch.Generator().manual_seed(42))

    print(f"Training set size: {len(train_set)}")
    print(f"Validation set size: {len(val_set)}")

    return LightningDataset(train_set, val_set, batch_size=batch_size, pin_memory=True, drop_last=True)


def tune_value_network(datamodule, value_config: ValueNetworkConfig):
    """
    Trains a value network using a given data module and saves the trained neural network.

    :param datamodule: The instance of a PyTorch Lightning `DataModule` class with tuning set
    :param value_config:
    """

    current_weights = value_config.weights_path
    value_network = load_value_net(ValueNetwork, current_weights)

    lr_monitor = LearningRateMonitor(logging_interval="epoch")

    # with DisableLogger() as DL, HiddenPrints() as HP:
    #     trainer = Trainer(accelerator="gpu",
    #                       devices=[0],
    #                       max_epochs=value_config.num_epoch,
    #                       callbacks=[lr_monitor],
    #                       gradient_clip_val=1.0,
    #                       enable_progress_bar=False)
    #
    #     trainer.fit(value_network, datamodule)
    #     val_score = trainer.validate(value_network, datamodule.val_dataloader())[0]
    #     trainer.save_checkpoint(current_weights)


    trainer = Trainer(accelerator="gpu",
                      devices=[0],
                      max_epochs=value_config.num_epoch,
                      callbacks=[lr_monitor],
                      gradient_clip_val=1.0,
                      enable_progress_bar=True)

    trainer.fit(value_network, datamodule)
    val_score = trainer.validate(value_network, datamodule.val_dataloader())[0]
    trainer.save_checkpoint(current_weights)

    #
    print(f"Value network balanced accuracy: {val_score['val_balanced_accuracy']}")


def run_training(extracted_retrons=None, value_config=None):

    """
    Performs the training stage in self-tuning process. Trains a value network using a set of processed molecules and
    saves the weights of the network.

    :param extracted_retrons: The path to the directory where the processed molecules extracted from planning
    :param value_config:
    """

    # create training set
    training_set = create_tuning_set(extracted_retrons=extracted_retrons, batch_size=value_config.batch_size)

    # retrain value network
    tune_value_network(datamodule=training_set, value_config=value_config)

def run_planning(targets_batch: list,
                 tree_config: TreeConfig,
                 policy_config: PolicyNetworkConfig,
                 value_config: ValueNetworkConfig,
                 reaction_rules_path: str,
                 building_blocks_path: str,
                 targets_batch_id: int):

    """
    Performs planning stage (tree search) for target molecules and save extracted from built trees retrons for further
    tuning the value network in the training stage.

    :param targets_batch:
    :param tree_config:
    :param policy_config:
    :param value_config:
    :param reaction_rules_path:
    :param building_blocks_path:
    :param targets_batch_id:
    """

    print(f'\nProcess batch number {targets_batch_id}')
    tree_list = []
    tree_config.silent = True
    for target in tqdm(targets_batch):

        try:
            tree = run_tree_search(target=target,
                                   tree_config=tree_config,
                                   policy_config=policy_config,
                                   value_config=value_config,
                                   reaction_rules_path=reaction_rules_path,
                                   building_blocks_path=building_blocks_path)
            tree_list.append(tree)

        except:
            continue

    num_solved = sum([len(i.winning_nodes) > 0 for i in tree_list])
    print(f"Planning is finished with {num_solved} solved targets")

    return tree_list


def run_reinforcement_tuning(targets_path: str,
                             tree_config: TreeConfig,
                             policy_config: PolicyNetworkConfig,
                             value_config: ValueNetworkConfig,
                             reinforce_config: ReinforcementConfig,
                             reaction_rules_path: str,
                             building_blocks_path: str,
                             results_root: str = None):
    """
    Performs self-tuning simulations with alternating planning and training stages

    :param targets_path:
    :param tree_config:
    :param policy_config:
    :param value_config:
    :param reinforce_config:
    :param reaction_rules_path:
    :param building_blocks_path:
    :param results_root:
    """

    # create results root folder
    results_root = Path(results_root)
    if not results_root.exists():
        results_root.mkdir()

    # load targets list
    with MoleculeReader(targets_path) as targets:
        targets = list(targets)

    # create value neural network
    value_config.weights_path = os.path.join(results_root, 'value_network.ckpt')
    value_network = create_value_network(value_config)

    # create targets batch
    targets_batch_list = create_targets_batch(targets, batch_size=reinforce_config.batch_size)

    # run reinforcement training
    for batch_id, targets_batch in enumerate(targets_batch_list, start=1):

        # start tree planning simulation for batch of targets
        tree_list = run_planning(targets_batch=targets_batch,
                                 tree_config=tree_config,
                                 policy_config=policy_config,
                                 value_config=value_config,
                                 reaction_rules_path=reaction_rules_path,
                                 building_blocks_path=building_blocks_path,
                                 targets_batch_id=batch_id)

        # extract pos and neg retrons from the list of built trees
        extracted_retrons = extract_tree_retrons(tree_list)

        # TODO there is a problem with batch size in lightning
        # train value network for extracted retrons
        run_training(extracted_retrons=extracted_retrons, value_config=value_config)
