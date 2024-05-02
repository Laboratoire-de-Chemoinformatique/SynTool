.. _value_network:

Value network
================

This page explains how to train a value network in SynTool.

Introduction
---------------------------

**Value network architecture**. During the evaluation step, the value function (or evaluation function) is used to estimate the retrosynthetic feasibility
of a newly created node. In SynTool, evaluation functions such as random function (assigns a random value), rollout function,
and value network trained with the reinforcement learning based algorithm are implemented. The architecture of the
value network is like the policy network. The molecular representation part of the neural network is the same, and the
difference is that the output linear layer returns a single value ranging from 0 to 1.

**Reinforcement value network tuning**. The value neural network is iteratively tuned on the training subsets of molecules
extracted from the simulated planning sessions. In the first iteration, the value network is initialized with random weights and
is used for the initial simulated retrosynthesis planning session for N target molecules. Then, retrons that were
part of a successful retrosynthesis routes leading to the building block molecules are labeled with a positive class, and
retron that did not lead to the building blocks are labeled with a negative class. This generated training data is
used to retrain the value network to better recognize retrons leading to possible successful retrosynthetic routes.
This is a classification problem, where the positive class corresponds to the retron that leads to building blocks;
otherwise, it is considered a negative class.

Configuration
---------------------------
The network architecture and training hyperparameters can be adjusted in the training configuration file below.

.. code-block:: yaml

    tree:
      max_iterations: 100
      max_tree_size: 10000
      max_time: 240
      max_depth: 9
      ucb_type: uct
      c_ucb: 0.1
      backprop_type: muzero
      search_strategy: expansion_first
      exclude_small: True
      min_mol_size: 6
      init_node_value: 0.5
      epsilon: 0
      silent: True
    node_evaluation:
      evaluation_type: rollout
      evaluation_agg: max
    node_expansion:
      top_rules: 50
      rule_prob_threshold: 0.0
      priority_rules_fraction: 0.5
    value_network:
      vector_dim: 512
      batch_size: 5
      dropout: 0.4
      learning_rate: 0.0005
      num_conv_layers: 5
      num_epoch: 100
    reinforcement:
      batch_size: 15
      num_simulations: 1

**Configuration parameters**:

.. table::
    :widths: 30 10 50

    ======================================== ================ ============
    Parameter                                Default          Description
    ======================================== ================ ============
    tree:max_iterations                      100              The maximum number of iterations the tree search algorithm will perform
    tree:max_tree_size                       10000            The maximum number of nodes that can be created in the search tree
    tree:max_time                            240              The maximum time (in seconds) for the tree search execution
    tree:max_depth                           9                The maximum depth of the tree, controlling how far the search can go from the root node
    tree:ucb_type                            uct              The type of Upper Confidence Bound (UCB) used in the tree search. Options include "puct" (predictive UCB), "uct" (standard UCB), and "value"
    tree:backprop_type                       muzero           The backpropagation method used during the tree search. Options are "muzero" (model-based approach) and "cumulative" (cumulative reward approach)
    tree:search_strategy                     expansion_first  The strategy for navigating the tree. Options are "expansion_first" (prioritizing the expansion of new nodes) and "evaluation_first" (prioritizing the evaluation of existing nodes)
    tree:exclude_small                       True             If True, excludes small molecules from the tree, typically focusing on more complex molecules
    tree:min_mol_size                        6                The minimum size of a molecule (the number of heavy atoms) to be considered in the search. Molecules smaller than this threshold are typically considered readily available building blocks
    tree:init_node_value                     0.5              The initial value for newly created nodes in the tree (for expansion_first search strategy)
    tree:epsilon                             0                This parameter is used in the epsilon-greedy strategy during the node selection, representing the probability of choosing a random action for exploration. A higher value leads to more exploration
    tree:silent                              True             If True, suppresses the progress logging of the tree search
    node_evaluation:evaluation_agg           max              The way the evaluation scores are aggregated. Options are "max" (using the maximum score) and "average" (using the average score)
    node_evaluation:evaluation_type          rollout          The method used for node evaluation. Options include "random" (random number between 0 and 1), "rollout" (using rollout simulations), and "gcn" (graph convolutional networks)
    node_expansion:top_rules                 50               The maximum amount of rules to be selected for node expansion from the list of predicted reaction rules
    node_expansion:rule_prob_threshold       0.0              The reaction rules with predicted probability lower than this parameter will be discarded
    node_expansion:priority_rules_fraction   0.5              The fraction of priority rules in comparison to the regular rules
    value_network:vector_dim                 512              The dimension of the hidden layers
    value_network:batch_size                 1000             The size of the batch of input molecular graphs
    value_network:dropout                    0.4              The dropout value
    value_network:learning_rate              0.0005           The learning rate
    value_network:num_conv_layers            5                The number of convolutional layers
    value_network:num_epoch                  100              The number of training epochs
    reinforcement:batch_size                 100              The size of the batch of target molecules used for planning simulation and value network update
    ======================================== ================ ============

CLI
---------------------------
Value network training can be performed with the below command.

.. code-block:: bash

    syntool reinforcement_value_network_training --config reinforcement.yaml --targets targets.smi --reaction_rules reaction_rules.pickle --building_blocks building_blocks.smi --policy_network policy_network.ckpt --results_dir value_network

**Parameters**:
    - ``config`` - the path to the configuration file.
    - ``targets`` - the path to the file with target molecules.
    - ``reaction_rules`` - the path to the file with reactions rules.
    - ``building_blocks`` - the path to the file with building blocks.
    - ``policy_network`` - the path to the file with trained policy network (ranking or filtering).
    - ``results_dir`` - the path to the directory where the trained value network will be to be stored.



