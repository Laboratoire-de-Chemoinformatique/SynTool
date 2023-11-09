"""
Module containing functions for running value network tuning with self-tuning approach
"""

import csv
import logging
from collections import defaultdict
from pathlib import Path
from random import shuffle

import torch
from CGRtools import smiles
from CGRtools.containers import MoleculeContainer
from CGRtools.files import SDFRead, SDFWrite
from pytorch_lightning import Trainer
from pytorch_lightning.callbacks import LearningRateMonitor
from pytorch_lightning.loggers import CSVLogger
from torch.utils.data import random_split
from torch_geometric.data import LightningDataset
from tqdm import tqdm

from Synto.interfaces.visualisation import to_table
from Synto.mcts.tree import Tree
from Synto.ml.networks.networks import ValueGraphNetwork
from Synto.ml.training.loading import load_value_net
from Synto.ml.training.preprocessing import ValueNetworkDataset
from Synto.ml.training.preprocessing import compose_retrons


def extract_tree_stats(tree):
    """
    Extracts various statistics from a tree, including the target smiles, tree size, search time, number of found paths,
    and the newick representation of the tree.

    :param tree: The built tree
    :return: A dictionary containing calculated statistics
    """
    newick_tree, newick_meta = tree.newickify(visits_threshold=1)
    newick_meta_line = ";".join([f"{nid},{v[0]},{v[1]},{v[2]}" for nid, v in newick_meta.items()])

    stats = {"target_smiles": str(tree.nodes[1]),
             "tree_size": len(tree),
             "search_time": float(round(tree.curr_time, 1)),
             "found_paths": len(tree.winning_nodes),
             "newick_tree": newick_tree,
             "newick_meta": newick_meta_line}

    return stats


def create_targets_batch(experiment_root=None, targets_file=None, tmp_file_id=None, batch_slices=None):
    """
    Takes in an experiment root directory, a targets file, a temporary file ID, and batch slices,
    and creates a batch file containing a subset of targets from the targets file.

    :param experiment_root: The root directory where the batch of targets will be stored
    :param targets_file: The path to a file containing the targets data in SDF format
    :param tmp_file_id: The unique identifier for the temporary batch file that will be created
    :param batch_slices: The list of indices that specify which molecules from the `targets_file` should be included
    in the batch
    :return: The path to the created batch file.
    """

    tmp_targets = experiment_root.joinpath("targets")
    if not tmp_targets.exists():
        tmp_targets.mkdir()
    with SDFRead(targets_file, indexable=True) as inp:
        inp.reset_index()
        file_length = len(inp)
        batch_slices = [i for i in batch_slices if i < file_length]
        targets = [inp[i] for i in batch_slices]
    batch_file = tmp_targets.joinpath(f"batch_{tmp_file_id}.sdf")
    with SDFWrite(batch_file) as out:
        for mol in targets:
            out.write(mol)
    return batch_file


def load_processed_molecules(path):
    """
    Reads a file containing processed molecules (extracted from tree retrons with their labels) and returns a dictionary
    where the molecules are the keys and the labels are the values.

    :param path: The path to the file containing the processed molecules data
    :return: A dictionary which contains the processed molecules and their corresponding labels
    """
    processed_molecules = defaultdict(float)
    with open(path, "r") as inp:
        _ = next(inp)  # skip header
        for line in inp:
            smi, reward = line.strip().split()
            reward = float(reward)
            processed_molecules[smi] = reward
    return processed_molecules


def shuffle_targets(targets_file):
    """
    The function shuffles the targets in a given set and writes new SDF

    :param targets_file: The file that contains a set of targets to be shuffled
    """
    with SDFRead(targets_file) as inp:
        mols = inp.read()
    shuffle(mols)
    with SDFWrite(targets_file) as out:
        for mol in mols:
            out.write(mol)
    del mols


def extract_tree_retrons(tree, processed_molecules=None):
    """
    Takes a built tree and a dictionary of processed molecules extracted from the previous trees as input, and returns
    the updated dictionary of processed molecules after adding the solved nodes from the given tree.

    :param tree: The built tree
    :param processed_molecules: The dictionary of precessed molecules extracted from the previous trees
    """

    if processed_molecules is None:
        processed_molecules = defaultdict(float)

    for idx, node in tree.nodes.items():
        # add solved nodes to set
        if node.is_solved():
            parent = idx
            while parent and parent != 1:
                composed_smi = str(compose_retrons(tree.nodes[parent].new_retrons))
                processed_molecules[composed_smi] = 1.0
                parent = tree.parents[parent]
        else:
            composed_smi = str(compose_retrons(tree.nodes[idx].new_retrons))
            processed_molecules[composed_smi] = 0.0

    return processed_molecules


def run_tree_search(target=None, config=None):
    """
    Takes a target molecule and a planning configuration dictionary as input, preprocesses the target molecule,
    initializes a tree and then runs the tree search algorithm.

    :param target: The target molecule. It can be either a `MoleculeContainer` object or a SMILES string
    :param config: The planning configuration that contains settings for tree search
    :return: The built tree
    """

    # preprocess target
    if isinstance(target, MoleculeContainer):
        target.canonicalize()
    elif isinstance(target, str):
        target = smiles(target)
        target.canonicalize()

    # initialize tree.
    tree = Tree(target=target, config=config)

    # remove target from buildings blocs
    if str(target) in tree.building_blocks:
        tree.building_blocks.remove(str(target))

    # run tree search
    _ = list(tree)

    return tree


def create_tuning_set(processed_molecules_path):
    """
    Creates a tuning dataset from a given processed molecules extracted from the trees from the
    planning stage and returns a LightningDataset object with a specified batch size for tuning value neural network.

    :param processed_molecules_path: The path to the directory where the processed molecules is stored
    :return: A LightningDataset object, which contains the tuning sets for value network tuning
    """

    full_dataset = ValueNetworkDataset(processed_molecules_path)
    train_size = int(0.8 * len(full_dataset))
    val_size = len(full_dataset) - train_size

    train_set, val_set = random_split(full_dataset, [train_size, val_size], torch.Generator().manual_seed(42))

    logging.info(f"Train Size: {len(train_set)}")
    logging.info(f"Val Size: {len(val_set)}")

    return LightningDataset(train_set, val_set, batch_size=256, pin_memory=True)


def tune_value_network(value_net, datamodule, experiment_root: Path, simul_id=0, n_epoch=100):
    """
    Trains a value network using a given data module and saves the trained neural network.

    :param value_net: The value network architecture with network weights
    :param datamodule: The instance of a PyTorch Lightning `DataModule` class with tuning set
    :param experiment_root: The root directory where the training log files and network weights will be saved
    :type experiment_root: Path
    :param simul_id: The identifier for the current simulation
    :param n_epoch: The number of training epochs in the value network tuning
    """

    weights_path = experiment_root.joinpath("weights")
    tdi = f"{simul_id}".zfill(3)
    current_weights = weights_path.joinpath(f"sim_{tdi}.ckpt")
    logs_path = experiment_root.joinpath("logs")

    lr_monitor = LearningRateMonitor(logging_interval="epoch")
    logger = CSVLogger(str(logs_path))

    trainer = Trainer(
        log_every_n_steps=5,
        accelerator="gpu",
        devices=[0],
        max_epochs=n_epoch,
        callbacks=[lr_monitor],
        logger=logger,
        gradient_clip_val=1.0,
    )

    trainer.fit(value_net, datamodule)
    val_score = trainer.validate(value_net, datamodule.val_dataloader())[0]
    logging.info(f"Training finished with loss: {val_score['val_loss']}; "
                 f"BA: {val_score['val_balanced_accuracy']}; F1: {val_score['val_f1_score']}")
    trainer.save_checkpoint(current_weights)


def run_training(processed_molecules_path=None, simul_id=None, config=None, experiment_root=None):
    """
    Performs the training stage in self-tuning process. Trains a value network using a set of processed molecules and
    saves the weights of the network.

    :param processed_molecules_path: The path to the directory where the processed molecules extracted from planning
    stage are stored
    :param simul_id: The simulation identifier
    :param config: The configuration dictionary that contains settings for the training process
    :param experiment_root: The root directory where the training log files and weights will be saved
    """

    weights_path = experiment_root.joinpath("weights")
    if not weights_path.exists():
        weights_path.mkdir()

    value_net = None
    if config["ValueNetwork"]["weights_path"]:
        config_weights_path = Path(config["ValueNetwork"]["weights_path"])
        if config_weights_path.exists():
            logging.info(f"Trainer loaded weights from {config_weights_path}")
            value_net = load_value_net(ValueGraphNetwork, config)

    if value_net is None:
        all_weigths = sorted(weights_path.glob("*.ckpt"))

        if all_weigths:
            config["ValueNetwork"]["weights_path"] = all_weigths[-1]
            logging.info(f"Trainer loaded weights from {all_weigths[-1]}")
            value_net = load_value_net(ValueGraphNetwork, config)

    training_set = create_tuning_set(processed_molecules_path)
    tune_value_network(value_net, training_set, experiment_root, simul_id, n_epoch=config["ValueNetwork"]["num_epoch"])


def run_planning(
        simul_id: int,
        config: dict,
        targets_file: Path,
        processed_molecules_path: Path = None,
        targets_batch_id: int = None
):
    """
    Performs planning stage (tree search) for target molecules and save extracted from built trees retrons for further
    tuning the value network in the training stage.

    :param simul_id: The simulation identifier
    :type simul_id: int
    :param config: The dictionary containing configuration settings for the planning stage
    :type config: dict
    :param targets_file: The path to the file containing the targets data
    :type targets_file: Path
    :param processed_molecules_path: The path to a file containing processed molecules from the previous planning stages.
    :type processed_molecules_path: Path
    :param targets_batch_id: The identifier of the batch of the targets
    :type targets_batch_id: int
    """

    experiment_root = Path(config['SelfTuning']['results_root'])

    # load value network
    if config["Tree"]["evaluation_mode"] == "gcn":
        value_net = None

        if config["ValueNetwork"]["weights_path"]:
            config_weights_path = Path(config["ValueNetwork"]["weights_path"])
            if config_weights_path.exists():
                logging.info(f"Simulation loaded weights from {config_weights_path}")
                value_net = load_value_net(ValueGraphNetwork, config)

        if value_net is None:
            weights_path = experiment_root.joinpath("weights")
            all_weights = sorted(weights_path.glob("*.ckpt"))

            if all_weights:
                config["ValueNetwork"]["weights_path"] = all_weights[-1]
                logging.info(f"Simulation loaded weights from {all_weights[-1]}")
                value_net = load_value_net(ValueGraphNetwork, config)

        if not value_net:
            logging.info(f"Trainer init model without loading weights")
            value_net = ValueGraphNetwork(
                vector_dim=config["ValueNetwork"]["vector_dim"],
                batch_size=config["ValueNetwork"]["batch_size"],
                dropout=config["ValueNetwork"]["dropout"],
                num_conv_layers=config["ValueNetwork"]["num_conv_layers"],
                learning_rate=config["ValueNetwork"]["learning_rate"],
            )
            #
            trainer = Trainer()
            trainer.strategy.connect(value_net)
            trainer.save_checkpoint(config["ValueNetwork"]["weights_path"])

    assert targets_file.suffix == ".sdf", "Only SDF files for list_of_molecules are acceptable"

    # load processed molecules (extracted retrons)
    processed_molecules = None
    if processed_molecules_path:
        if processed_molecules_path.exists():
            logging.info(f"Loading labelled list_of_molecules from {str(processed_molecules_path)}")
            processed_molecules = load_processed_molecules(processed_molecules_path)

    if processed_molecules is None:
        logging.info("Labelled list_of_molecules were not loaded")

    # simulation folder
    simulation_folder = experiment_root.joinpath(f"simulation_{simul_id}")
    if not simulation_folder.exists():
        simulation_folder.mkdir()

    stats_header = ["target_smiles", "tree_size", "search_time", "found_paths", "newick_tree", "newick_meta"]

    if targets_batch_id is not None:
        stats_file = simulation_folder.joinpath(f"tree_stats_sim_{simul_id}_batch_{targets_batch_id}.csv")
    else:
        stats_file = simulation_folder.joinpath(f"tree_stats_sim_{simul_id}.csv")

    # read targets file
    num_solved, total_time = 0, 0
    with SDFRead(targets_file, indexable=True) as inp, open(stats_file, "w", newline="\n") as csvfile:
        inp.reset_index()

        batch_len = len(inp)
        stats_writer = csv.DictWriter(csvfile, delimiter=",", fieldnames=stats_header)
        stats_writer.writeheader()

        # run tree search for targets
        config["Tree"]["verbose"] = False
        for target_id, target in tqdm(enumerate(inp), total=batch_len):
            tree = run_tree_search(target, config)
            processed_molecules = extract_tree_retrons(tree, processed_molecules=processed_molecules)

            # extract tree statistics
            tree_stats = extract_tree_stats(tree)
            if tree_stats["found_paths"] > 0:
                num_solved += 1
            total_time += tree_stats["search_time"]

            # write tree statistics
            stats_writer.writerow(tree_stats)
            csvfile.flush()
            if targets_batch_id is not None:
                saved_paths = simulation_folder.joinpath(
                    f"paths_target_{target_id}_sim_{simul_id}_batch_{targets_batch_id}.html"
                )
            else:
                saved_paths = simulation_folder.joinpath(
                    f"paths_target_{target_id}_sim_{simul_id}.html"
                )

            # save tree retro paths table
            to_table(tree, str(saved_paths), extended=True)

    logging.info(f"Simulation over batch is finished with mean search time {total_time // batch_len} "
                 f"and percetage of solved queries {(num_solved / batch_len) * 100}")

    # shuffle retrons
    processed_keys = list(processed_molecules.keys())
    shuffle(processed_keys)
    processed_molecules = {i: processed_molecules[i] for i in processed_keys}

    # write final file with extracted retrons
    with open(processed_molecules_path, "w") as out:
        out.write("smiles\tlabel\n")
        for smi, reward in processed_molecules.items():
            out.write(f"{smi}\t{reward}\n")
    del processed_molecules


def run_self_tuning(config: dict):
    """
    Performs self-tuning simulations with alternating planning and training stages

    :param config: The configuration settings for the self-tuning process
    :type config: dict
    """

    restart_batch = -1

    experiment_root = Path(config['SelfTuning']['results_root'])
    targets_file = Path(config['SelfTuning']['dataset_path'])

    # create results root folder
    if not experiment_root.exists():
        experiment_root.mkdir()

    logging_file = experiment_root.joinpath('self_tuning.log')
    logging.basicConfig(filename=logging_file, encoding='utf-8', level=10,
                        format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%d/%m/%Y %I:%M:%S %p')

    with SDFRead(targets_file, indexable=True) as inp:
        inp.reset_index()
        file_length = len(inp)

    num_simulations = config['SelfTuning']['num_simulations']
    for simul_id in range(num_simulations):
        processed_molecules_path = experiment_root.joinpath(f"simulation_{simul_id}",
                                                            f"tree_retrons_sim_{simul_id}.smi")

        batch_size = config['SelfTuning']['batch_size']
        for batch_id in range(file_length // batch_size + int(bool(file_length % batch_size))):

            if restart_batch > batch_id:
                logging.info(f"Skipped batch {batch_id} for simulation {simul_id}")
            else:
                restart_batch = -1
                logging.info(f"Started simulation {simul_id} for batch {batch_id}")

                # create batch of targets
                batch_slices = range(batch_id * batch_size, (batch_id + 1) * batch_size)
                targets_batch_file = create_targets_batch(experiment_root=experiment_root,
                                                          targets_file=targets_file,
                                                          tmp_file_id=batch_id,
                                                          batch_slices=batch_slices)

                # start tree planning simulation for batch of targets
                run_planning(
                    simul_id=simul_id,
                    config=config,
                    targets_file=targets_batch_file,
                    processed_molecules_path=processed_molecules_path,
                    targets_batch_id=batch_id
                )

                # train value network for extracted retrons
                run_training(processed_molecules_path=processed_molecules_path,
                             simul_id=simul_id,
                             config=config,
                             experiment_root=experiment_root)

            # shuffle targets
            shuffle_targets(targets_file)