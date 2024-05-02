"""
Module containing a class Tree that used for tree search of retrosynthetic paths
"""

import logging
from collections import deque, defaultdict
from math import sqrt
from random import choice, uniform
from time import time
from typing import Dict, Set, List, Tuple

from CGRtools.containers import MoleculeContainer
from CGRtools import smiles
from numpy.random import uniform
from tqdm.auto import tqdm
from SynTool.utils.loading import load_building_blocks, load_reaction_rules
from SynTool.chem.reaction import Reaction, apply_reaction_rule
from SynTool.chem.retron import Retron
from SynTool.mcts.evaluation import ValueFunction
from SynTool.mcts.expansion import PolicyFunction
from SynTool.mcts.node import Node
from SynTool.utils.config import TreeConfig
from typing import Iterator, List, Tuple, Union


class Tree:
    """
    Tree class with attributes and methods for Monte-Carlo tree search.
    """

    def __init__(self,
                 target: Union[MoleculeContainer, str],
                 config: TreeConfig,
                 reaction_rules_path: str,
                 building_blocks_path: str,
                 policy_function: PolicyFunction,
                 value_function: ValueFunction = None):
        """
        Initializes a tree object with optional parameters for tree search for target molecule.

        :param target: A target molecule for retrosynthesis routes search.
        :param config: A tree configuration.
        :param reaction_rules_path: A path for reaction rules file.
        :param building_blocks_path: A path for building blocks file.
        :param policy_function: A loaded policy function.
        :param value_function: A loaded value function. If None, the rollout is used as a default for node evaluation.
        """

        # config parameters
        self.config = config

        # check target
        if isinstance(target, str):
            target = smiles(target)
        assert (bool(target)), "Target is not defined, is not a MoleculeContainer or have no atoms"
        if target:
            target.canonicalize()

        target_retron = Retron(target, canonicalize=True)
        target_retron.prev_retrons.append(Retron(target, canonicalize=True))
        target_node = Node(retrons_to_expand=(target_retron,), new_retrons=(target_retron,))

        # tree structure init
        self.nodes: Dict[int, Node] = {1: target_node}
        self.parents: Dict[int, int] = {1: 0}
        self.children: Dict[int, Set[int]] = {1: set()}
        self.winning_nodes: List[int] = list()
        self.visited_nodes: Set[int] = set()
        self.expanded_nodes: Set[int] = set()
        self.nodes_visit: Dict[int, int] = {1: 0}
        self.nodes_depth: Dict[int, int] = {1: 0}
        self.nodes_prob: Dict[int, float] = {1: 0.0}
        self.nodes_rules: Dict[int, float] = {}
        self.nodes_init_value: Dict[int, float] = {1: 0.0}
        self.nodes_total_value: Dict[int, float] = {1: 0.0}

        # tree building limits
        self.curr_iteration: int = 0
        self.curr_tree_size: int = 2
        self.curr_time: float = 2

        # utils
        self._tqdm = True # TODO tqdm cannot be pickled, needed to disable it with multiproc module

        # policy and value functions
        self.policy_function = policy_function
        if self.config.evaluation_type == "gcn":
            if value_function is None:
                raise ValueError("Value function not specified while evaluation mode is 'gcn'")
            else:
                self.value_function = value_function

        # building blocks and reaction reaction_rules
        self.reaction_rules = load_reaction_rules(reaction_rules_path)
        self.building_blocks = load_building_blocks(building_blocks_path)

    def __len__(self) -> int:
        """
        Returns the current size (the number of nodes) in the tree.
        """

        return self.curr_tree_size - 1

    def __iter__(self) -> "Tree":
        """
        The function is defining an iterator for a Tree object. Also needed for the bar progress display.
        """

        self._start_time = time()
        if self._tqdm:
            self._tqdm = tqdm(total=self.config.max_iterations, disable=self.config.silent)
        return self

    def __repr__(self) -> str:
        """
        Returns a string representation of the tree (target SMILES, tree size, and the number of found paths).
        """
        return self.report()

    def __next__(self) -> [bool, List[int]]:
        """
        The __next__ method is used to do one iteration of the tree building.

        :return: Returns True if the route was found and the node id of the last node in the route.
        Otherwise, returns False and the id of the last visited node.
        """

        if self.nodes[1].curr_retron.is_building_block(self.building_blocks, self.config.min_mol_size):
            raise StopIteration("Target is building block.")

        if self.curr_iteration >= self.config.max_iterations:
            raise StopIteration("Iterations limit exceeded.")
        elif self.curr_tree_size >= self.config.max_tree_size:
            raise StopIteration("Max tree size exceeded or all possible paths found.")
        elif self.curr_time >= self.config.max_time:
            raise StopIteration("Time limit exceeded.")

        # start new iteration
        self.curr_iteration += 1
        self.curr_time = time() - self._start_time

        if self._tqdm:
            self._tqdm.update()

        curr_depth, node_id = 0, 1  # start from the root node_id

        explore_path = True
        while explore_path:
            self.visited_nodes.add(node_id)

            if self.nodes_visit[node_id]:  # already visited
                if not self.children[node_id]:  # dead node
                    logging.debug(f"Tree search: bumped into node {node_id} which is dead")
                    self._update_visits(node_id)
                    explore_path = False
                else:
                    node_id = self._select_node(node_id)  # select the child node
                    curr_depth += 1
            else:
                if self.nodes[node_id].is_solved():  # found path
                    self._update_visits(node_id)  # this prevents expanding of bb node_id
                    self.winning_nodes.append(node_id)
                    return True, [node_id]

                elif curr_depth < self.config.max_depth:  # expand node if depth limit is not reached
                    self._expand_node(node_id)
                    if not self.children[node_id]:  # node was not expanded
                        logging.debug(f"Tree search: node {node_id} was not expanded")
                        value_to_backprop = -1.0
                    else:
                        self.expanded_nodes.add(node_id)

                        if self.config.search_strategy == "evaluation_first":
                            # recalculate node value based on children synthesisability and backpropagation
                            child_values = [self.nodes_init_value[child_id] for child_id in self.children[node_id]]

                            if self.config.evaluation_agg == "max":
                                value_to_backprop = max(child_values)

                            elif self.config.evaluation_agg == "average":
                                value_to_backprop = sum(child_values) / len(self.children[node_id])

                        elif self.config.search_strategy == "expansion_first":
                            value_to_backprop = self._get_node_value(node_id)

                    # backpropagation
                    self._backpropagate(node_id, value_to_backprop)
                    self._update_visits(node_id)
                    explore_path = False

                    if self.children[node_id]:
                        # found after expansion
                        found_after_expansion = set()
                        for child_id in iter(self.children[node_id]):
                            if self.nodes[child_id].is_solved():
                                found_after_expansion.add(child_id)
                                self.winning_nodes.append(child_id)

                        if found_after_expansion:
                            return True, list(found_after_expansion)

                else:
                    self._backpropagate(node_id, self.nodes_total_value[node_id])
                    self._update_visits(node_id)
                    explore_path = False

        return False, [node_id]

    def _ucb(self, node_id: int) -> float:
        """
        Calculates the Upper Confidence Bound (UCB) statistics for a given node.

        :param node_id: The id of the node.

        :return: The calculated UCB.
        """

        prob = self.nodes_prob[node_id]  # Predicted by policy network score
        visit = self.nodes_visit[node_id]

        if self.config.ucb_type == "puct":
            u = (self.config.c_ucb * prob * sqrt(self.nodes_visit[self.parents[node_id]])) / (visit + 1)
            return self.nodes_total_value[node_id] + u
        elif self.config.ucb_type == "uct":
            u = (self.config.c_ucb * sqrt(self.nodes_visit[self.parents[node_id]]) / (visit + 1))
            return self.nodes_total_value[node_id] + u
        elif self.config.ucb_type == "value":
            return self.nodes_init_value[node_id] / (visit + 1)

    def _select_node(self, node_id: int) -> int:
        """
        Selects a node based on its UCB value and returns the id of the node with the highest UCB.

        :param node_id: The id of the node.

        :return: The id of the node with the highest UCB.
        """

        if self.config.epsilon > 0:
            n = uniform(0, 1)
            if n < self.config.epsilon:
                return choice(list(self.children[node_id]))

        best_score, best_children = None, []
        for child_id in self.children[node_id]:
            score = self._ucb(child_id)
            if best_score is None or score > best_score:
                best_score, best_children = score, [child_id]
            elif score == best_score:
                best_children.append(child_id)

        return best_children[0] # TODO choice(best_children) were replaced for the reproducibility

    def _expand_node(self, node_id: int) -> None:
        """
        Expands the node by generating new retrons with policy (expansion) function.

        :param node_id: The id the node to be expanded.

        :return: None.
        """
        curr_node = self.nodes[node_id]
        prev_retrons = curr_node.curr_retron.prev_retrons

        tmp_retrons = set()
        for prob, rule, rule_id in self.policy_function.predict_reaction_rules(curr_node.curr_retron, self.reaction_rules):
            for products in apply_reaction_rule(curr_node.curr_retron.molecule, rule):
                # check repeated products
                if not products or not set(products) - tmp_retrons:
                    continue
                tmp_retrons.update(products)

                for molecule in products:
                    molecule.meta["reactor_id"] = rule_id

                new_retrons = tuple(Retron(mol) for mol in products)
                scaled_prob = prob * len(list(filter(lambda x: len(x) > self.config.min_mol_size, products)))

                if set(prev_retrons).isdisjoint(new_retrons):
                    retrons_to_expand = (*curr_node.next_retrons, *(x for x in new_retrons if not x.is_building_block(
                                         self.building_blocks, self.config.min_mol_size)))

                    child_node = Node(retrons_to_expand=retrons_to_expand, new_retrons=new_retrons)

                    for new_retron in new_retrons:
                        new_retron.prev_retrons = [new_retron, *prev_retrons]

                    self._add_node(node_id, child_node, scaled_prob, rule_id)

    def _add_node(self, node_id: int, new_node: Node, policy_prob: float = None, rule_id: int = None) -> None:
        """
        Adds a new node to the tree with probability of reaction rules predicted by policy function and applied to the
        parent node of the new node.

        :param node_id: The id of the parent node.
        :param new_node: The new node to be added.
        :param policy_prob: The probability of reaction rules predicted by policy function for thr parent node.

        :return: None.
        """

        new_node_id = self.curr_tree_size

        self.nodes[new_node_id] = new_node
        self.parents[new_node_id] = node_id
        self.children[node_id].add(new_node_id)
        self.children[new_node_id] = set()
        self.nodes_visit[new_node_id] = 0
        self.nodes_prob[new_node_id] = policy_prob
        self.nodes_rules[new_node_id] = rule_id
        self.nodes_depth[new_node_id] = self.nodes_depth[node_id] + 1
        self.curr_tree_size += 1

        if self.config.search_strategy == "evaluation_first":
            node_value = self._get_node_value(new_node_id)
        elif self.config.search_strategy == "expansion_first":
            node_value = self.config.init_node_value

        self.nodes_init_value[new_node_id] = node_value
        self.nodes_total_value[new_node_id] = node_value

    def _get_node_value(self, node_id: int) -> float:
        """
        Calculates the value for the given node (for example with rollout or value network).

        :param node_id: The id of the node to be evaluated.

        :return: The estimated value of the node.
        """

        node = self.nodes[node_id]

        if self.config.evaluation_type == "random":
            node_value = uniform()

        elif self.config.evaluation_type == "rollout":
            node_value = min((self._rollout_node(retron, current_depth=self.nodes_depth[node_id])
                              for retron in node.retrons_to_expand), default=1.0)

        elif self.config.evaluation_type == "gcn":
            node_value = self.value_function.predict_value(node.new_retrons)

        return node_value

    def _update_visits(self, node_id: int) -> None:
        """
        Updates the number of visits from the current node to the root node.

        :param node_id: The id of the current node.

        :return: None.
        """

        while node_id:
            self.nodes_visit[node_id] += 1
            node_id = self.parents[node_id]

    def _backpropagate(self, node_id: int, value: float) -> None:
        """
        Backpropagates the value through the tree from the current.

        :param node_id: The id of the node from which to backpropagate the value.
        :param value: The value to backpropagate.

        :return: None.
        """
        while node_id:
            if self.config.backprop_type == "muzero":
                self.nodes_total_value[node_id] = (
                self.nodes_total_value[node_id] * self.nodes_visit[node_id] + value) / (self.nodes_visit[node_id] + 1)
            elif self.config.backprop_type == "cumulative":
                self.nodes_total_value[node_id] += value
            node_id = self.parents[node_id]

    def _rollout_node(self, retron: Retron, current_depth: int = None) -> float:
        """
        Performs a rollout simulation from a given node in the tree.
        Given the current retron, find the first successful reaction and return the new retrons.

        If the retron is a building_block, return 1.0, else check the first successful reaction.

        If the reaction is not successful, return -1.0.

        If the reaction is successful, but the generated retrons are not the building_blocks and the retrons
        cannot be generated without exceeding current_depth threshold, return -0.5.

        If the reaction is successful, but the retrons are not the building_blocks and the retrons
        cannot be generated, return -1.0.

        :param retron: The retron to be evaluated.
        :param current_depth: The current depth of the tree.

        :return: The reward (value) assigned to the retron.
        """

        max_depth = self.config.max_depth - current_depth

        # retron checking
        if retron.is_building_block(self.building_blocks, self.config.min_mol_size):
            return 1.0

        if max_depth == 0:
            print('max depth reached in the beginning')

        # retron simulating
        occurred_retrons = set()
        retrons_to_expand = deque([retron])
        history = defaultdict(dict)
        rollout_depth = 0
        while retrons_to_expand:
            # Iterate through reactors and pick first successful reaction.
            # Check products of the reaction if you can find them in in-building_blocks data
            # If not, then add missed products to retrons_to_expand and try to decompose them
            if len(history) >= max_depth:
                reward = -0.5
                return reward

            current_retron = retrons_to_expand.popleft()
            history[rollout_depth]["target"] = current_retron
            occurred_retrons.add(current_retron)

            # Pick the first successful reaction while iterating through reactors
            reaction_rule_applied = False
            for prob, rule, rule_id in self.policy_function.predict_reaction_rules(current_retron, self.reaction_rules):
                for products in apply_reaction_rule(current_retron.molecule, rule):
                    if products:
                        reaction_rule_applied = True
                        break

                if reaction_rule_applied:
                    history[rollout_depth]["rule_index"] = rule_id
                    break

            if not reaction_rule_applied:
                reward = -1.0
                return reward

            products = tuple(Retron(product) for product in products)
            history[rollout_depth]["products"] = products

            # check loops
            if any(x in occurred_retrons for x in products) and products:
                # sometimes manual can create a loop, when
                # print('occurred_retrons')
                reward = -1.0
                return reward

            if occurred_retrons.isdisjoint(products):
                # added number of atoms check
                retrons_to_expand.extend([x for x in products
                                          if not x.is_building_block(self.building_blocks, self.config.min_mol_size)])
                rollout_depth += 1

        reward = 1.0
        return reward


    def report(self) -> str:
        """
        Returns the string representation of the tree.
        """

        return (f"Tree for: {str(self.nodes[1].retrons_to_expand[0])}\n"
                f"Number of nodes: {len(self)}\n"
                f"Number of visited nodes: {len(self.visited_nodes)}\n"
                f"Number of found routes: {len(self.winning_nodes)}\n"
                f"Number of iterations: {self.curr_iteration}\n"
                f"Time: {round(self.curr_time, 1)} seconds")

    def path_score(self, node_id: int) -> float:
        """
        Calculates the score of a given route from the current node to the root node.
        The score depends on cumulated node values nad the route length.

        :param node_id: The id of the current given node.

        :return: The route score.
        """

        cumulated_nodes_value, path_length = 0, 0
        while node_id:
            path_length += 1

            cumulated_nodes_value += self.nodes_total_value[node_id]
            node_id = self.parents[node_id]

        return cumulated_nodes_value / (path_length ** 2)

    def path_to_node(self, node_id: int) -> List[Node, ]:
        """
        Returns the route (list of id of nodes) to from the node current node to the root node.

        :param node_id: The id of the current node.

        :return: The list of nodes.
        """

        nodes = []
        while node_id:
            nodes.append(node_id)
            node_id = self.parents[node_id]
        return [self.nodes[node_id] for node_id in reversed(nodes)]

    def synthesis_path(self, node_id: int) -> Tuple[Reaction,]:
        """
        Given a node_id, return a tuple of reactions that represent the retrosynthesis path from the current node.

        :param node_id: The id of the current node.

        :return: The tuple of extracted reactions representing the synthesis route.
        """

        nodes = self.path_to_node(node_id)

        tmp = [Reaction([x.molecule for x in after.new_retrons], [before.curr_retron.molecule])
               for before, after in zip(nodes, nodes[1:])]  # TODO tmp variable name is not meaningful

        for r in tmp:
            r.clean2d()
        return tuple(reversed(tmp))

    def newickify(self, visits_threshold: int = 0, root_node_id: int = 1):  # TODO what is return here ?
        """
        Adopted from https://stackoverflow.com/questions/50003007/how-to-convert-python-dictionary-to-newick-form-format.

        :param visits_threshold: The minimum number of visits for the given node  # TODO is this explanation correct ?
        :param root_node_id: The id of the root node.

        :return: The newick string and meta dict.
        """
        visited_nodes = set()

        def newick_render_node(current_node_id: int) -> str:
            """
            Recursively generates a Newick string representation of the tree.

            :param current_node_id: The id of the current node.

            :return: A string representation of a node in a Newick format.
            """
            assert (
                current_node_id not in visited_nodes
            ), "Error: The tree may not be circular!"
            node_visit = self.nodes_visit[current_node_id]

            visited_nodes.add(current_node_id)
            if self.children[current_node_id]:
                # Nodes
                children = [
                    child
                    for child in list(self.children[current_node_id])
                    if self.nodes_visit[child] >= visits_threshold
                ]
                children_strings = [newick_render_node(child) for child in children]
                children_strings = ",".join(children_strings)
                if children_strings:
                    return f"({children_strings}){current_node_id}:{node_visit}"
                else:
                    # Leafs within threshold
                    return f"{current_node_id}:{node_visit}"
            else:
                # Leafs
                return f"{current_node_id}:{node_visit}"

        newick_string = newick_render_node(root_node_id) + ";"

        meta = {}
        for node_id in iter(visited_nodes):
            node_value = round(self.nodes_total_value[node_id], 3)

            node_synthesisability = round(self.nodes_init_value[node_id])

            visit_in_node = self.nodes_visit[node_id]
            meta[node_id] = (node_value, node_synthesisability, visit_in_node)

        return newick_string, meta
