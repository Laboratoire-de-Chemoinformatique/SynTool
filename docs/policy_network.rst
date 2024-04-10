Policy network
===========================

This page explains how to do a policy network training in SynTool.

Introduction
---------------------------
The tree nodes in MCTS are expanded by an expansion function approximated by a policy neural network.
The policy network is composed of two parts: molecular representation and prediction parts. The first part is
responsible for creating a numerical representation of molecule structure (Graph Convolution Network (GCN) blocks
and summation over atoms). The prediction part depends on the type of policy network: filtering or ranking policy
network. All the reaction rules predicted by the policy neural network are sorted by probability and the top 50 of
them are selected to be applied to the current intermediate product in the MCTS expansion step.

**Ranking policy network**. The ranking policy network is trained on a reaction dataset as a multi-class classification. Each reaction corresponds
to a vector in which the position of the positive class corresponds to a reaction rule extracted from that reaction.
All other extracted reaction rules are assigned as negative classes. The size of the class vector corresponds to the
total number of reaction rules. This approach biases the ranking policy network to prioritize reaction rules that are
likely to produce reactions similar to real ones.

**Filtering policy network**. In a filtering policy network, the prediction part is formed from two linear layers with a sigmoid activation function
that assigns the probabilities for the “regular”, as well as “priority” reaction rules, which include such
transformations as cyclization. These two vectors are then combined with a coefficient α ranging from 0 to 1.
This approach ensures that the priority reaction rules receive the highest score, followed by other regular reaction
rules. The multi-class regular and priority vectors for training the filtering policy network are obtained by applying
all reaction rules to the set of training molecules (these molecules can be extracted from any database). If the
reaction rule is successfully applied and creates a new precursor, it will be assigned a positive class in the regular
reaction rules vector, otherwise a negative class. In addition, if the reaction rule splits the molecule into two or
more structures with several heavy atoms of more than 6 or opens a cycle, the priority vector gets a positive class,
otherwise negative.

Configuration
---------------------------
The network architecture and training hyperparameters can be adjusted in the training configuration file below.

.. code-block:: yaml

    vector_dim: 512
    batch_size: 1000
    dropout: 0.4
    learning_rate: 0.0005
    num_conv_layers: 5
    num_epoch: 100

**Configuration parameters**:

    - `vector_dim` - the dimension of the hidden layers.
    - `batch_size` - the size of the batch of input molecular graphs.
    - `dropout` - the dropout value.
    - `learning_rate` - the learning rate.
    - `num_conv_layers` - the number of convolutional layers.
    - `num_epoch` - the number of training epochs.

CLI
---------------------------
Ranking and filtering policy network training can be performed with the below commands.

**Ranking policy network**

.. code-block:: bash

    syntool supervised_ranking_policy_training --config policy.yaml --reaction_data reaction_data_filtered.smi --reaction_rules reaction_rules.pickle --results_dir ranking_policy_network

**Parameters**:
    - `--config` is the path to the configuration file.
    - `--reaction_data` is the path to the file with reactions for ranking policy training.
    - `--reaction_rules` is the path to the file with extracted reaction rules.
    - `--results_dir` is the path to the directory where the trained policy network will be stored.

**Filtering policy network**

.. code-block:: bash

    syntool supervised_filtering_policy_training --config policy.yaml --molecules_data molecules_data.smi --reaction_rules reaction_rules.pickle --results_dir filtering_policy_network

**Parameters**:
    - `--config` is the path to the configuration file.
    - `--reaction_data` is the path to the file with molecules for filtering policy training.
    - `--reaction_rules` is the path to the file with extracted reaction rules.
    - `--results_dir` is the path to the directory where the trained policy network will be stored.
