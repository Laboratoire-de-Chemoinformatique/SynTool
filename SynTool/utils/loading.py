"""Module containing functions for loading reaction rules, building blocks and
retrosynthetic models."""

import functools
import pickle
from abc import ABCMeta
from typing import List, Set

from CGRtools.reactor.reactor import Reactor
from torch import device

from SynTool.ml.networks.policy import PolicyNetwork
from SynTool.ml.networks.value import ValueNetwork
from SynTool.utils.files import MoleculeReader


@functools.lru_cache(maxsize=None)
def load_reaction_rules(file: str) -> List[Reactor]:
    """Loads the reaction rules from a pickle file and converts them into a
    list of Reactor objects if necessary.

    :param file: The path to the pickle file that stores the reaction
        rules.
    :return: A list of reaction rules as Reactor objects.
    """

    with open(file, "rb") as f:
        reaction_rules = pickle.load(f)

    if not isinstance(reaction_rules[0][0], Reactor):
        reaction_rules = [Reactor(x) for x, _ in reaction_rules]

    return reaction_rules


@functools.lru_cache(maxsize=None)
def load_building_blocks(building_blocks_path: str) -> Set[str]:
    """Loads building blocks data from a file and returns a frozen set of
    building blocks.

    :param building_blocks_path: The path to the file containing the
        building blocks.
    :return: The frozen set loaded building blocks.
    """

    # TODO remove later
    if building_blocks_path.split(".")[-1] == "pickle":
        with open(building_blocks_path, "rb") as f:
            building_blocks = pickle.load(f)
            # building_blocks = set(str(i) for i in building_blocks)
            return building_blocks

    with MoleculeReader(building_blocks_path) as molecules:
        building_blocks = set(str(mol) for mol in molecules)

    return building_blocks


def load_value_net(model_class: ValueNetwork, value_network_path: str) -> ValueNetwork:
    """Loads the value network.

    :param value_network_path: The path to the file storing value
        network weights.
    :param model_class: The model class to be loaded.
    :return: The loaded value network.
    """

    map_location = device("cpu")
    return model_class.load_from_checkpoint(value_network_path, map_location)


def load_policy_net(model_class: ABCMeta, policy_network_path: str) -> PolicyNetwork:
    """Loads the policy network.

    :param policy_network_path: The path to the file storing policy
        network weights.
    :param model_class: The model class to be loaded.
    :return: The loaded policy network.
    """

    map_location = device("cpu")
    return model_class.load_from_checkpoint(
        policy_network_path, map_location, batch_size=1
    )
