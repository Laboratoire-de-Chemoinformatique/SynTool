Value network
================

This page explains how to train a value network in SynTool.

Introduction
---------------------------

During the evaluation step, the value function (or evaluation function) is used to estimate the retrosynthetic feasibility
of a newly created node. In Syntool, evaluation functions such as random function (assigns a random value), rollout function,
and value network trained with the learning from simulated experience algorithm are implemented. The architecture of the
value network is like the policy network. The molecular representation part of the neural network is the same, and the
difference is that the output linear layer returns a single value ranging from 0 to 1.

The value neural network is iteratively trained on training subsets extracted from the previous planning sessions
(learning from simulated experience). In the first iteration, the value network is initialized with random weights and
is used for the initial retrosynthesis planning session for N target molecules. Then, intermediate products that were
part of a successful retrosynthesis path leading to building block molecules are labeled with a positive label, and
precursors that did not lead to building blocks are labeled with a negative label. This generated training data is
used to retrain the value network to better recognize precursors leading to possible successful retrosynthetic paths.
The training task of the value network is a classification problem, where the positive class corresponds to the precursor
that leads to building blocks; otherwise, it is considered a negative class.

Configuration
---------------------------
The network architecture and training hyperparameters can be adjusted in the training configuration file below. The value network, its architecture, and hyperparameters can be specified in the ValueNetwork section in the training configuration file:

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

    - `tree/max_iterations` - the maximum number of iterations the tree search algorithm will perform.
    - `tree/max_tree_size` - the maximum number of nodes that can be created in the search tree.
    - `tree/max_time` - the maximum time (in seconds) for the tree search execution.
    - `tree/max_depth` - the maximum depth of the tree, controlling how far the search can go from the root node.
    - `tree/ucb_type` - the type of Upper Confidence Bound (UCB) used in the tree search. Options include "puct" (predictive UCB), "uct" (standard UCB), and "value".
    - `tree/c_ucb` - the parameter controlling the exploration-exploitation balance in UCB, which influences how much the algorithm favors the exploration of new paths versus the exploitation of known paths.
    - `tree/backprop_type` - the backpropagation method used during the tree search. Options are "muzero" (model-based approach) and "cumulative" (cumulative reward approach).
    - `tree/search_strategy` - the strategy for navigating the tree. Options are "expansion_first" (prioritizing the expansion of new nodes) and "evaluation_first" (prioritizing the evaluation of existing nodes).
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
    - `value_network/vector_dim` - the dimension of the hidden layers.
    - `value_network/batch_size` - the size of the batch of input molecular graphs.
    - `value_network/dropout` - the dropout value.
    - `value_network/learning_rate` - the learning rate.
    - `value_network/num_conv_layers` - the number of convolutional layers.
    - `value_network/num_epoch` - the number of training epochs.
    - `batch_size/batch_size` - the size of the batch of the target molecules used for planning simultation and value network update.
    - `batch_size/num_simulations` - the number of training epochs.


CLI
---------------------------
Value network training can be performed with the below command.

.. code-block:: bash

    syntool reinforcement_value_network_training --config reinforcement.yaml --targets targets.smi --reaction_rules reaction_rules.pickle --building_blocks building_blocks.smi --policy_network ranking_policy_network/policy_network.ckpt --results_dir value_network

**Parameters**:
    - `--config` is the path to the configuration file.
    - `--targets` is the path to the file with target molecules.
    - `--reaction_rules` is the path to the file with reactions rules.
    - `--building_blocks` is the path to the file with building blocks.
    - `--policy_network` is the path to the file with trained policy network (ranking or filtering).
    - `--results_dir` is the path to the directory where the trained value network will be to be stored.



