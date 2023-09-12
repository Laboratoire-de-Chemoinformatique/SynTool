"""
Module containing a class that represents a policy function for node expansion in the search tree
"""

import torch

from Synto.chem.retron import Retron
from Synto.networks.networks import PolicyNetwork
from Synto.training.loading import load_policy_net
from Synto.training.preprocessing import mol_to_pyg


class PolicyFunction:
    """
    Policy function based on policy neural network for node expansion in MCTS
    """

    def __init__(self, config: dict):
        """
        Initializes the expansion function (filter policy network).

        :param config: A dictionary containing configuration settings for the expansion policy
        :type config: dict
        """

        self.top_rules = config['PolicyNetwork']['top_rules']
        self.threshold = config['PolicyNetwork']['rule_prob_threshold']
        self.priority_rules_fraction = config['PolicyNetwork']['priority_rules_fraction']

        self.policy_net = load_policy_net(PolicyNetwork, config)
        self.policy_net.eval()

    def predict_reaction_rules(self, retron: Retron, reaction_rules: list):
        """
        The policy function predicts reaction rules based on a given retron and return a list of predicted reaction rules.

        :param retron: The current retron for which the reaction rules are predicted
        :type retron: Retron
        :param reaction_rules: The list of reaction rules from which applicable reaction rules are predicted
        and selected.
        :type reaction_rules: list
        """

        pyg_graph = mol_to_pyg(retron.molecule)
        if pyg_graph:
            with torch.no_grad():
                probs, priority = self.policy_net.forward(pyg_graph)
            del pyg_graph
        else:
            return []

        probs = probs[0].double()
        priority = priority[0].double()
        priority_coef = self.priority_rules_fraction
        probs = (1 - priority_coef) * probs + priority_coef * priority
        #
        sorted_probs, sorted_rules = torch.sort(probs, descending=True)
        sorted_probs, sorted_rules = sorted_probs[:self.top_rules], sorted_rules[:self.top_rules]

        sorted_probs = torch.softmax(sorted_probs, -1)
        sorted_probs, sorted_rules = sorted_probs.tolist(), sorted_rules.tolist()

        for prob, rule_id in zip(sorted_probs, sorted_rules):
            if prob > self.threshold:
                yield prob, reaction_rules[rule_id], rule_id