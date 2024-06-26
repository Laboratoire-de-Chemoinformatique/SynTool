"""Module containing functions for running value network tuning with self-
tuning approach."""

import os
import random
from collections import defaultdict
from pathlib import Path
from random import shuffle
from typing import Dict, List

import torch
from CGRtools.containers import MoleculeContainer
from pytorch_lightning import Trainer
from torch.utils.data import random_split
from torch_geometric.data.lightning import LightningDataset

from SynTool.chem.retron import compose_retrons
from SynTool.mcts.evaluation import ValueNetworkFunction
from SynTool.mcts.expansion import PolicyNetworkFunction
from SynTool.mcts.tree import Tree
from SynTool.ml.networks.value import ValueNetwork
from SynTool.ml.training.preprocessing import ValueNetworkDataset
from SynTool.utils.config import (PolicyNetworkConfig, ReinforcementConfig,
                                  TreeConfig, ValueNetworkConfig)
from SynTool.utils.files import MoleculeReader
from SynTool.utils.loading import (load_building_blocks, load_reaction_rules,
                                   load_value_net)
from SynTool.utils.logging import DisableLogger, HiddenPrints


def create_value_network(value_config: ValueNetworkConfig) -> ValueNetwork:
    """Creates the initial value network.

    :param value_config: The value network configuration.
    :return: The valueNetwork to be trained/tuned.
    """

    weights_path = Path(value_config.weights_path)
    value_network = ValueNetwork(
        vector_dim=value_config.vector_dim,
        batch_size=value_config.batch_size,
        dropout=value_config.dropout,
        num_conv_layers=value_config.num_conv_layers,
        learning_rate=value_config.learning_rate,
    )

    with DisableLogger(), HiddenPrints():
        trainer = Trainer()
        trainer.strategy.connect(value_network)
        trainer.save_checkpoint(weights_path)

    return value_network


def create_targets_batch(
    targets: List[MoleculeContainer], batch_size: int
) -> List[List[MoleculeContainer]]:
    """Creates the targets batches for planning simulations and value network
    tuning.

    :param targets: The list of target molecules.
    :param batch_size: The size of each target batch.
    :return: The list of lists corresponding to each target batch.
    """

    num_targets = len(targets)
    batch_splits = list(
        range(num_targets // batch_size + int(bool(num_targets % batch_size)))
    )

    if int(num_targets / batch_size) == 0:
        print(f"1 batch were created with {num_targets} molecules")
    else:
        print(
            f"{len(batch_splits)} batches were created with {batch_size} molecules each"
        )

    targets_batch_list = []
    for batch_id in batch_splits:
        batch_slices = [
            i
            for i in range(batch_id * batch_size, (batch_id + 1) * batch_size)
            if i < len(targets)
        ]
        targets_batch_list.append([targets[i] for i in batch_slices])

    return targets_batch_list


def run_tree_search(
    target: MoleculeContainer,
    tree_config: TreeConfig,
    policy_config: PolicyNetworkConfig,
    value_config: ValueNetworkConfig,
    reaction_rules_path: str,
    building_blocks_path: str,
) -> Tree:
    """Runs tree search for the given target molecule.

    :param target: The target molecule.
    :param tree_config: The planning configuration of tree search.
    :param policy_config: The policy network configuration.
    :param value_config: The value network configuration.
    :param reaction_rules_path: The path to the file with reaction
        rules.
    :param building_blocks_path: The path to the file with building
        blocks.
    :return: The built search tree for the given molecule.
    """

    # policy and value function loading
    policy_function = PolicyNetworkFunction(policy_config=policy_config)
    value_function = ValueNetworkFunction(weights_path=value_config.weights_path)
    reaction_rules = load_reaction_rules(reaction_rules_path)
    building_blocks = load_building_blocks(building_blocks_path)

    # initialize tree
    tree_config.silent = True
    tree = Tree(
        target=target,
        config=tree_config,
        reaction_rules=reaction_rules,
        building_blocks=building_blocks,
        expansion_function=policy_function,
        evaluation_function=value_function,
    )
    tree._tqdm = False

    # remove target from buildings blocs
    if str(target) in tree.building_blocks:
        tree.building_blocks.remove(str(target))

    # run tree search
    _ = list(tree)

    return tree


def extract_tree_retrons(tree_list: List[Tree]) -> Dict[str, float]:
    """Takes the built tree and extracts the retrons for value network tuning.
    The retrons from found retrosynthetic routes are labeled as a positive
    class and retrons from not solved routes are labeled as a negative class.

    :param tree_list: The list of built search trees.

    :return: The dictionary with the retron SMILES and its class (positive - 1 or negative - 0).
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


def balance_extracted_retrons(extracted_retrons):
    extracted_retrons_balanced = {}
    neg_list = [i for i, j in extracted_retrons.items() if j == 0]
    for k, v in extracted_retrons.items():
        if v == 1:
            extracted_retrons_balanced[k] = v
        if len(extracted_retrons_balanced) < len(neg_list):
            neg_list.pop(random.choice(range(len(neg_list))))
    return extracted_retrons_balanced


def create_tuning_set(
    extracted_retrons: Dict[str, float], batch_size: int = 1
) -> LightningDataset:
    """Creates the value network tuning dataset from retrons extracted from the
    planning simulation.

    :param extracted_retrons: The dictionary with the extracted retrons
        and their labels.
    :param batch_size: The size of the batch in value network tuning.
    :return: A LightningDataset object, which contains the tuning set
        for value network tuning.
    """

    extracted_retrons = balance_extracted_retrons(extracted_retrons)

    full_dataset = ValueNetworkDataset(extracted_retrons)
    train_size = int(0.6 * len(full_dataset))
    val_size = len(full_dataset) - train_size

    train_set, val_set = random_split(
        full_dataset, [train_size, val_size], torch.Generator().manual_seed(42)
    )

    print(f"Training set size: {len(train_set)}")
    print(f"Validation set size: {len(val_set)}")

    return LightningDataset(
        train_set, val_set, batch_size=batch_size, pin_memory=True, drop_last=True
    )


def tune_value_network(
    datamodule: LightningDataset, value_config: ValueNetworkConfig
) -> None:
    """Trains the value network using a given tuning data and saves the trained
    neural network.

    :param datamodule: The tuning dataset (LightningDataset).
    :param value_config: The value network configuration.
    :return: None.
    """

    current_weights = value_config.weights_path
    value_network = load_value_net(ValueNetwork, current_weights)

    with DisableLogger(), HiddenPrints():
        trainer = Trainer(
            accelerator="gpu",
            devices=[0],
            max_epochs=value_config.num_epoch,
            enable_checkpointing=False,
            logger=False,
            gradient_clip_val=1.0,
            enable_progress_bar=False,
        )

        trainer.fit(value_network, datamodule)
        val_score = trainer.validate(value_network, datamodule.val_dataloader())[0]
        trainer.save_checkpoint(current_weights)

    # trainer = Trainer(
    #     accelerator="gpu",
    #     devices=[0],
    #     max_epochs=value_config.num_epoch,
    #     enable_checkpointing=False,
    #     logger=False,
    #     gradient_clip_val=1.0,
    #     enable_progress_bar=True,
    # )
    #
    # trainer.fit(value_network, datamodule)
    # val_score = trainer.validate(value_network, datamodule.val_dataloader())[0]
    # trainer.save_checkpoint(current_weights)

    #
    print(f"Value network balanced accuracy: {val_score['val_balanced_accuracy']}")


def run_training(
    extracted_retrons: Dict[str, float] = None, value_config: ValueNetworkConfig = None
) -> None:
    """Runs the training stage in reinforcement value network tuning.

    :param extracted_retrons: The retrons extracted from the planing
        simulations.
    :param value_config: The value network configuration.
    :return: None.
    """

    # create training set
    training_set = create_tuning_set(
        extracted_retrons=extracted_retrons, batch_size=value_config.batch_size
    )

    # retrain value network
    tune_value_network(datamodule=training_set, value_config=value_config)


#
# def run_planning(
#     targets_batch: List[MoleculeContainer],
#     tree_config: TreeConfig,
#     policy_config: PolicyNetworkConfig,
#     value_config: ValueNetworkConfig,
#     reaction_rules_path: str,
#     building_blocks_path: str,
#     targets_batch_id: int,
# ) -> List[Tree]:
#     """Performs the planning stage for the batch of target molecules.
#
#     :param targets_batch: The batch of target molecules for planning simulation.
#     :param tree_config: The search tree configuration.
#     :param policy_config: The policy network configuration.
#     :param value_config: The value network configuration.
#     :param reaction_rules_path: The path to the file with reaction rules.
#     :param building_blocks_path: The path to the file with building blocks.
#     :param targets_batch_id: The id of the batch of target molecules.
#     :return: The list of built trees for the given batch of target molecules.
#     """
#
#     search_batch = [
#         (
#             target,
#             tree_config,
#             policy_config,
#             value_config,
#             reaction_rules_path,
#             building_blocks_path,
#         )
#         for target in targets_batch
#     ]
#
#     print(f"\nProcess batch number {targets_batch_id}")
#     with Pool(2) as pool:
#         tree_list = pool.starmap(run_tree_search, search_batch)
#
#     num_solved = sum(len(i.winning_nodes) > 0 for i in tree_list)
#     print(f"Planning is finished with {num_solved} solved targets")
#
#     return tree_list


def run_planning(
    targets_batch: List[MoleculeContainer],
    tree_config: TreeConfig,
    policy_config: PolicyNetworkConfig,
    value_config: ValueNetworkConfig,
    reaction_rules_path: str,
    building_blocks_path: str,
    targets_batch_id: int,
):
    """Performs planning stage (tree search) for target molecules and save
    extracted from built trees retrons for further tuning the value network in
    the training stage.

    :param targets_batch:
    :param tree_config:
    :param policy_config:
    :param value_config:
    :param reaction_rules_path:
    :param building_blocks_path:
    :param targets_batch_id:
    """
    from tqdm import tqdm

    print(f"\nProcess batch number {targets_batch_id}")
    tree_list = []
    tree_config.silent = False
    for target in tqdm(targets_batch):

        try:
            tree = run_tree_search(
                target=target,
                tree_config=tree_config,
                policy_config=policy_config,
                value_config=value_config,
                reaction_rules_path=reaction_rules_path,
                building_blocks_path=building_blocks_path,
            )
            tree_list.append(tree)

        except Exception as e:
            print(e)
            continue

    num_solved = sum([len(i.winning_nodes) > 0 for i in tree_list])
    print(f"Planning is finished with {num_solved} solved targets")

    return tree_list


def run_reinforcement_tuning(
    targets_path: str,
    tree_config: TreeConfig,
    policy_config: PolicyNetworkConfig,
    value_config: ValueNetworkConfig,
    reinforce_config: ReinforcementConfig,
    reaction_rules_path: str,
    building_blocks_path: str,
    results_root: str = None,
) -> None:
    """Performs reinforcement value network tuning.

    :param targets_path: The path to the file with target molecules.
    :param tree_config: The search tree configuration.
    :param policy_config: The policy network configuration.
    :param value_config: The value network configuration.
    :param reinforce_config: The reinforcement tuning configuration.
    :param reaction_rules_path: The path to the file with reaction
        rules.
    :param building_blocks_path: The path to the file with building
        blocks.
    :param results_root: The path to the directory where trained value
        network will be saved.
    :return: None.
    """

    # create results root folder
    results_root = Path(results_root)
    if not results_root.exists():
        results_root.mkdir()

    # load targets list
    with MoleculeReader(targets_path) as targets:
        targets = list(targets)

    # create value neural network
    value_config.weights_path = os.path.join(results_root, "value_network.ckpt")
    create_value_network(value_config)

    # create targets batch
    targets_batch_list = create_targets_batch(
        targets, batch_size=reinforce_config.batch_size
    )

    # run reinforcement training
    for batch_id, targets_batch in enumerate(targets_batch_list, start=1):

        # start tree planning simulation for batch of targets
        tree_list = run_planning(
            targets_batch=targets_batch,
            tree_config=tree_config,
            policy_config=policy_config,
            value_config=value_config,
            reaction_rules_path=reaction_rules_path,
            building_blocks_path=building_blocks_path,
            targets_batch_id=batch_id,
        )

        # extract pos and neg retrons from the list of built trees
        extracted_retrons = extract_tree_retrons(tree_list)

        # train value network for extracted retrons
        run_training(extracted_retrons=extracted_retrons, value_config=value_config)
