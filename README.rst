SynTool - Synthesis planning tool
========
SynTool is a tool for chemical synthesis planning based on Monte-Carlo Tree Search (MCTS)
with various implementations of policy and value functions.

Installation
------------

Important: all versions require **python from 3.8 and up to 3.10**!

Linux distributions
^^^^^^^^^^^

It requires only poetry 1.3.2. To install poetry, follow the example below, or the instructions on
https://python-poetry.org/docs/#installation

For example, on Ubuntu we can install miniconda and set an environment in which we will install poetry with the following commands:

.. code-block:: bash

    # install miniconda
    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
    bash Miniconda3-latest-Linux-x86_64.sh

    # install poetry
    conda create -n syntool -c conda-forge "poetry=1.3.2" "python=3.10" -y
    conda activate syntool

    # install SynTool
    git clone https://github.com/Laboratoire-de-Chemoinformatique/Syntool.git

    # navigate to the SynTool folder and run the following command:
    cd SynTool/
    poetry install --with gpu

If Poetry fails with error, a possible solution is to update the bashrc file with the following command:

.. code-block:: bash

    echo 'export PYTHON_KEYRING_BACKEND=keyring.backends.null.Keyring' >> ~/.bashrc
    exec "bash"

Optional
^^^^^^^^^^^
After installation, one can add the Synto environment in their Jupyter platform:

.. code-block:: bash

    python -m ipykernel install --user --name synto --display-name "syntool"

Usage
------------
The usage is mostly optimized for the command line interface.
Here are implemented commands:

* download_planning_data
* download_training_data
* building_blocks
* reaction_mapping
* reaction_standardizing
* reaction_filtering
* rule_extracting
* supervised_ranking_policy_training
* supervised_filtering_policy_training
* reinforcement_value_network_training

Each command has a description that can be called with ``syntool --help`` and ``syntool command --help``


Run training from scratch
^^^^^^^^^^^
.. code-block:: bash

    cd tests

    # download training data
    syntool download_training_data --root_dir tests

    # standardize building blocks
    syntool building_blocks --input tests/building_blocks.smi --output tests/building_blocks_2.smi

    # reaction data mapping
    syntool reaction_mapping --input tests/uspto_original.smi --output tests/uspto_mapped.smi

    # reaction data standardizing
    syntool reaction_standardizing --config configs/standardization.yaml --input tests/uspto_mapped.smi --output tests/uspto_standardized.smi

    # reaction data filtering
    syntool reaction_filtering --config configs/filtration.yaml --input tests/uspto_standardized.smi --output tests/uspto_filtered.smi

    # filtering reaction rule extracting
    syntool rule_extracting --config configs/extraction.yaml --input tests/uspto_filtered.smi --output tests/reaction_rules.pickle

    # supervised ranking policy training
    syntool supervised_ranking_policy_training --config configs/policy.yaml --reaction_data tests/uspto_filtered.smi --reaction_rules tests/reaction_rules.pickle --results_dir tests/ranking_policy_network

    # reinforcement value network training
    syntool reinforcement_value_network_training --config configs/reinforcement.yaml --targets targets.smi --reaction_rules tests/reaction_rules.pickle --building_blocks tests/building_blocks.smi --policy_network tests/ranking_policy_network/weights/policy_network.ckpt --results_dir tests/value_network


Run retrosynthetic planning
^^^^^^^^^^^
.. code-block:: bash

    cd tests
    # download planning data
    syntool download_planning_data --root_dir tests

    # or run retrosynthesis planning from trained retrosynthetic models
    # planning with rollout evaluation (value network=None)
    syntool planning --config configs/planning.yaml --targets targets.smi --reaction_rules tests/reaction_rules.pickle --building_blocks tests/building_blocks.smi --policy_network tests/ranking_policy_network/weights/policy_network.ckpt --results_dir tests/planning

    # planning with value network evaluation
    syntool planning --config configs/planning.yaml --targets targets.smi --reaction_rules tests/reaction_rules.pickle --building_blocks tests/building_blocks.smi --policy_network tests/ranking_policy_network/weights/policy_network.ckpt --value_network tests/value_network/weights/value_network.ckpt --results_dir tests/planning

Documentation
-----------

The detailed documentation can be found `here <https://laboratoire-de-chemoinformatique.github.io/Syntool/>`_

