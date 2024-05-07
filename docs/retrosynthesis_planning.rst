.. _retrosynthesis_planning:

Retrosynthesis planning
========================

This page explains how to perform a retrosynthesis planning with tree search in SynTool.

Introduction
---------------------------
In SynTool retrosynthesis planning module combines the search algorithm (MCTS), reaction rules, and policy function for
their prediction in node expansion and value function (rollout function or value network) in node evaluation.
The planning is coupled with a visualization module for the display of found retrosynthesis routes.

Tree search
---------------------------
The retrosynthesis planning in SynTool is executed with the MCTS algorithm. The nodes in the MCTS algorithm are expanded
by the expansion function predicting reaction rules applicable to the current precursor and evaluated by
the evaluation function navigating the tree exploration in the promising directions. The tree search is limited
by tree parameters: number of iterations, time of the search, and size of the tree (total number of nodes).
Retrosynthesis planning in SynTool can be performed using two search strategies:
the evaluation-first and the expansion-first strategy.

**Expansion-first strategy.** In the expansion-first strategy, each newly created node is assigned a predefined constant value.
This approach is characterized by a more stochastic selection of nodes for expansion but allows for a reduction in the
computational resources.

**Evaluation-first strategy.** In the evaluation-first strategy, each newly created node immediately is evaluated with
the evaluation function, which allows for more exhaustive tree exploration. Although the node evaluation in the
evaluation-first strategy imposes an additional computational overhead, this problem can be overcome by the application
of fast evaluation functions, such as one approximated by a value neural network.

**Rollout evaluation.** The current implementation of rollout evaluation in SynTool is described here. For the given precursor,
a policy network predicts a set of applicable reaction rules sorted by their predicted probability. Then all reaction rules
are applied one by one and the first successfully applied reaction rule from this set generates new precursors. Then, the policy network
predicts the reaction rules for obtained precursors. This dissection proceeds until the stop criterion is reached with the corresponding value:

    - If the precursor is a building_block, return 1.0
    - If the reaction is not successful, return -1.0 (all predicted reaction rules are not applicable).
    - If the reaction is successful, but the generated precursors are not the building_blocks and cannot be generated without exceeding the maximum tree depth, return -0.5.
    - If the reaction is successful, but the precursors are not the building_blocks and cannot be generated, return -1.0.

Configuration
---------------------------
The retrosynthesis planning algorithm can be adjusted by the configuration yaml file:

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
      rule_prob_threshold: 0.0
      priority_rules_fraction: 0.5

**Configuration parameters**:

.. table::
    :widths: 45 10 50

    ======================================== ================ ==========================================================
    Parameter                                Default          Description
    ======================================== ================ ==========================================================
    tree:max_iterations                      100              The maximum number of iterations the tree search algorithm will perform
    tree:max_tree_size                       10000            The maximum number of nodes that can be created in the search tree
    tree:max_time                            240              The maximum time (in seconds) for the tree search execution
    tree:max_depth                           9                The maximum depth of the tree, controlling how far the search can go from the root node
    tree:ucb_type                            uct              The type of Upper Confidence Bound (UCB) used in the tree search. Options include "puct" (predictive UCB), "uct" (standard UCB), and "value" (the initial node value)
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
    node_expansion:priority_rules_fraction   0.5              The fraction of priority rules in comparison to the regular rules (only for filtering policy)
    ======================================== ================ ==========================================================

CLI
---------------------------
Retrosynthesis planning can be performed with the below command.
If you use your custom building blocks, be sure to canonicalize them before planning.

.. code-block:: bash

    syntool building_blocks --input building_blocks_init.smi --output building_blocks_stand.smi
    syntool planning --config planning.yaml --targets targets.smi --reaction_rules reaction_rules.pickle --building_blocks building_blocks_stand.smi --policy_network policy_network.ckpt --results_dir planning

**Parameters**:
    - ``config`` - the path to the configuration file.
    - ``targets`` - the path to the file with target molecule for retrosynthesis planning.
    - ``reaction_rules`` - the path to the file with reaction rules.
    - ``building_blocks`` - the path to the file with building blocks.
    - ``policy_network`` - the path to the file with trained policy network (ranking or filtering).
    - ``value_network`` - the path to the file with trained value network if available (default is None).
    - ``results_dir`` - the path to the directory where the trained value network will be to be stored.

Results analysis
---------------------------
After the retrosynthesis planning is finished, the planning results will be stored to the determined directory.
This directory will contain the following directories/files:

- `tree_search_stats.csv` – the CSV table with planning statistics.
- `extracted_routes.json` – the retrosynthesis routes extracted from the search trees. Can be used for route analysis with programming utils.
- `extracted_routes_html` – the directory containing html files with visualized retrosynthesis routes extracted from the search trees. Can be used for the visual analysis of the extracted retrosynthesis routes.
