"""
Module containing functions for loading reaction rules, building blocks and retrosynthetic models.
"""

import functools
import logging
import pickle
from time import time
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
from torch import device
from CGRtools.reactor.reactor import Reactor
from CGRtools import SMILESRead
from SynTool.ml.networks.value import ValueNetwork
from SynTool.ml.networks.policy import PolicyNetwork
from abc import ABCMeta
from typing import List, Set


@functools.lru_cache(maxsize=None)
def load_reaction_rules(file: str) -> List[Reactor]:
    """
    Loads the reaction rules from a pickle file and converts them into a list of Reactor objects if necessary.

    :param file: The path to the pickle file that stores the reaction rules.

    :return: A list of reaction rules as Reactor objects.
    """

    with open(file, "rb") as f:
        reaction_rules = pickle.load(f)

    if not isinstance(reaction_rules[0][0], Reactor):
        reaction_rules = [Reactor(x) for x, _ in reaction_rules]

    return reaction_rules


@functools.lru_cache(maxsize=None)
def load_building_blocks(file: str, canonicalize: bool = False) -> Set[str]:
    """
    Loads building blocks data from a file, either in text, SMILES, or pickle format, and returns a frozen set of
    building blocks.

    :param file: The path to the file containing the building blocks.
    :param canonicalize: If True, canonicalizes the SMILES of the building blocks.

    :return: The frozen set loaded building blocks.
    """

    if not file:
        logging.warning("No external In-Stock data was loaded")
        return None

    start = time()
    if isinstance(file, FileStorage):
        filename = secure_filename(file.filename)
        if filename.endswith(".pickle") or filename.endswith(".pkl"):
            bb = pickle.load(file)
        elif filename.endswith(".txt") or filename.endswith(".smi"):
            bb = set([mol.decode("utf-8") for mol in file])
        else:
            raise TypeError(
                "content of FileStorage is not appropriate for in-building_blocks dataloader, expected .txt, .smi, .pickle or .pkl"
            )
    elif isinstance(file, str):
        filetype = file.split(".")[-1]
        # Loading in-building_blocks substances data
        if filetype in {"txt", "smi", "smiles"}:
            with open(file, "r") as file:
                if canonicalize:
                    parser = SMILESRead.create_parser(ignore=True)
                    mols = [parser(str(mol)) for mol in file]
                    for mol in mols:
                        mol.canonicalize()
                    bb = set([str(mol).strip() for mol in mols])
                else:
                    bb = set([str(mol).strip() for mol in file])
        elif filetype == "pickle" or filetype == "pkl":
            with open(file, "rb") as file:
                bb = pickle.load(file)
                if isinstance(bb, list):
                    bb = set(bb)
        else:
            raise TypeError(
                f"expected .txt, .smi, .pickle, or .pkl files, not {filetype}"
            )

    stop = time()
    logging.debug(f"{len(bb)} In-Stock Substances are loaded.\nTook {round(stop - start, 2)} seconds.")
    return bb


def load_value_net(model_class: ABCMeta, value_network_path: str) -> ValueNetwork:
    """
    Loads the value network.

    :param value_network_path: The path to the file storing value network weights.
    :param model_class: The model class to be loaded.

    :return: The loaded value network.
    """

    map_location = device("cpu")
    return model_class.load_from_checkpoint(value_network_path, map_location)


def load_policy_net(model_class: ABCMeta, policy_network_path: str) -> PolicyNetwork:
    """
    Loads the policy network.

    :param policy_network_path: The path to the file storing policy network weights.
    :param model_class: The model class to be loaded.

    :return: The loaded policy network.
    """

    map_location = device("cpu")
    return model_class.load_from_checkpoint(policy_network_path, map_location, batch_size=1)

