.. _policy_network:

Policy network
===========================

This page explains how to do a policy network training in SynTool.

Introduction
---------------------------
The tree nodes in MCTS are expanded by an expansion function approximated by a policy graph neu-ral network.
The policy network is composed of two parts: molecular representation and reaction rule prediction parts.
In the representation part, the molecular graph is converted to a single vector by graph convolutional layers.
The training set structure and the prediction part architecture depend on the type of policy network,
particularly the ranking or filtering policy network.

**Ranking policy network**. The training dataset for ranking policy network consists of pairs of reactions and
corresponding reaction rules extracted from it. The products of the reaction are transformed to the CGR encoded
as a molecular graph with the one-hot encoded label vector where the positive label corresponds to the reaction rule.
The prediction part is terminated with the softmax function generating the “probability of successful application” of
each reaction rule to a given input molecular graph, which can be used for the reaction rules “ranking”.

**Filtering policy network**. The training dataset for the filtering policy is formed by the application of all
reaction rules to the training molecules. The labels vector is filled with positive labels in positions corresponding
to the successfully applied reaction rules. The prediction part of the filtering policy is formed from two linear layers
with a sigmoid function that assigns the probabilities for the “regular”, as well as “priority” reac-tion rules
(cyclization reaction rules). These two vectors are then combined with a coefficient α ranging from 0 to 1.
This approach ensures that the priority reaction rules receive the highest score, followed by other regular reaction rules.

**Conclusion**. The filtering policy network requires much more computational resources for the generating of the training dataset than
the ranking policy but can be used with any set of reaction rules because the original reaction dataset is not needed.
This allows for the portability of reaction rules extracted with another software from any source of reaction data.

Configuration
---------------------------
The ranking or filtering policy network architecture and training hyperparameters can be adjusted in the training configuration yaml file below.

.. code-block:: yaml

    vector_dim: 512
    num_conv_layers: 5
    learning_rate: 0.0005
    dropout: 0.4
    num_epoch: 100
    batch_size: 1000

**Configuration parameters**:

.. table::
    :widths: 20 10 50

    ================================== ======= =========================================================================
    Parameter                          Default  Description
    ================================== ======= =========================================================================
    vector_dim                         512     The dimension of the hidden layers
    num_conv_layers                    5       The number of convolutional layers
    learning_rate                      0.0005  The learning rate
    dropout                            0.4     The dropout value
    num_epoch                          100     The number of training epochs
    batch_size                         1000    The size of the training batch of input molecular graphs
    ================================== ======= =========================================================================

CLI
---------------------------
Ranking and filtering policy network training can be performed with the below commands.

**Ranking policy network**

.. code-block:: bash

    syntool supervised_ranking_policy_training --config policy.yaml --reaction_data reaction_data_filtered.smi --reaction_rules reaction_rules.pickle --results_dir ranking_policy_network

**Parameters**:
    - ``config`` - the path to the configuration file.
    - ``reaction_data`` - the path to the file with reactions for ranking policy training.
    - ``reaction_rules`` - the path to the file with extracted reaction rules.
    - ``results_dir`` - the path to the directory where the trained policy network will be stored.

**Filtering policy network**

.. code-block:: bash

    syntool supervised_filtering_policy_training --config policy.yaml --molecule_data molecules_data.smi --reaction_rules reaction_rules.pickle --results_dir filtering_policy_network

**Parameters**:
    - ``config`` - the path to the configuration file.
    - ``molecule_data`` - the path to the file with molecules for filtering policy training.
    - ``reaction_rules`` - the path to the file with extracted reaction rules.
    - ``results_dir`` - the path to the directory where the trained policy network will be stored.
