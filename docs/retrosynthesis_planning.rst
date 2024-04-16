.. _retrosynthesis_planning:

Retrosynthesis planning
================

This page explains how to perform a retrosynthesis planning with tree search in SynTool.

Introduction
---------------------------
In SynTool retrosynthesis planning module combines the search algorithm (MCTS), reaction rules, and policy function for
their prediction in node expansion and value function (rollout function or value network) in node evaluation.
The planning is coupled with a visualization module for the display of found retrosynthetic routes.

Configuration
---------------------------
The retrosynthesis planning algorithm can be adjusted by the configuration file:

.. code-block:: yaml

    tree:
      max_iterations: 100
      max_tree_size: 10000
      max_time: 1200
      max_depth: 9
      ucb_type: uct
      c_ucb: 0.1
      backprop_type: muzero
      search_strategy: expansion_first
      exclude_small: True
      init_node_value: 0.5
      min_mol_size: 6
      silent: True
    node_evaluation:
      evaluation_type: rollout
      evaluation_agg: max
    node_expansion:
      top_rules: 50
      rule_prob_threshold: 0.5
      priority_rules_fraction: 0.5

**Configuration parameters**:

    - `tree/max_iterations` - the maximum number of iterations the tree search algorithm will perform.
    - `tree/max_tree_size` - the maximum number of nodes that can be created in the search tree.
    - `tree/max_time` - the maximum time (in seconds) for the tree search execution.
    - `tree/max_depth` - the maximum depth of the tree, controlling how far the search can go from the root node.
    - `tree/ucb_type` - the type of Upper Confidence Bound (UCB) used in the tree search. Options include "puct" (predictive UCB), "uct" (standard UCB), and "value".
    - `tree/c_ucb` - the parameter controlling the exploration-exploitation balance in UCB, which influences how much the algorithm favors the exploration of new paths versus the exploitation of known paths.
    - `tree/backprop_type` - the backpropagation method used during the tree search. Options are "muzero" (model-based approach) and "cumulative" (cumulative reward approach).
    - `tree/search_strategy` - the strategy for navigating the tree. Options are "expansion_first" (prioritizing the expansion of new nodes) and "evaluation_first" (prioritizing the evaluation of new nodes).
    - `tree/exclude_small` - if True, excludes small molecules from the tree, typically focusing on more complex molecules.
    - `tree/init_node_value` - the initial value for newly created nodes in the tree. This can impact how nodes are prioritized during the search.
    - `tree/epsilon` - this parameter is used in the epsilon-greedy strategy during node selection, representing the probability of choosing a random action for exploration. A higher value leads to more exploration.
    - `tree/min_mol_size` - the minimum size of a molecule (in terms of the number of heavy atoms) to be considered in the search. Molecules smaller than this threshold are typically considered readily available building blocks.
    - `tree/silent` - if True, suppresses the progress logging of the tree search.
    - `node_evaluation/evaluation_agg` - the way the evaluation scores are aggregated. Options are "max" (using the maximum score) and "average" (using the average score).
    - `node_evaluation/evaluation_type` - the method used for node evaluation. Options include "random" (random number between 0 and 1), "rollout" (using rollout simulations), and "gcn" (graph convolutional networks).
    - `node_expansion/top_rules` - the maximum amount of rules to be selected for node expansion from the list of predicted reaction rules.
    - `node_expansion/rule_prob_threshold` - the reaction rules with predicted probability lower than this parameter will be discarded.
    - `node_expansion/priority_rules_fraction` - the fraction of priority rules in comparison to th regular rules.

CLI
---------------------------
Retrosynthesis planning can be performed with the below command.

**Retrosynthesis planning with rollout evaluation**

.. code-block:: bash

    syntool planning --config planning.yaml --targets targets.smi --reaction_rules reaction_rules.pickle --building_blocks building_blocks.smi --policy_network policy_network.ckpt --results_dir planning

**Parameters**:
    - `config` - the path to the configuration file.
    - `targets` - the path to the file with target molecule for retrosynthesis planning.
    - `reaction_rules` - the path to the file with reaction rules.
    - `building_blocks` - the path to the file with building blocks.
    - `policy_network` - the path to the file with trained policy network (ranking or filtering).
    - `results_dir` - the path to the directory where the trained value network will be to be stored.

**Retrosynthesis planning with value network evaluation**

.. code-block:: bash

    syntool planning --config planning.yaml --targets targets.smi --reaction_rules reaction_rules.pickle --building_blocks building_blocks.smi --policy_network policy_network.ckpt --value_network value_network.ckpt --results_dir planning

**Parameters**:
    - `config` - the path to the configuration file.
    - `targets` - the path to the file with target molecule for retrosynthesis planning.
    - `reaction_rules` - the path to the file with reaction rules.
    - `building_blocks` - the path to the file with building blocks.
    - `policy_network` - the path to the file with trained policy network (ranking or filtering).
    - `value_network` - the path to the file with trained value network (ranking or filtering).
    - `results_dir` - the path to the directory where the trained value network will be to be stored.


