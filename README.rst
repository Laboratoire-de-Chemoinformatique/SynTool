
SynTool - a tool for synthesis planning
========================================
SynTool is a tool for reaction data curation, reaction rules extraction, retrosynthetic models training,
and retrosynthesis planning. This is a multilayered software allowing for processing any source of
reaction data and building a ready-to-use retrosynthesis planner.

Installation
------------

**Important-1:** all versions require **python from 3.8 and up to 3.10**!

**Important-2:** currently for neural networks training GPU is necessary!

Linux distributions
^^^^^^^^^^^^^^^^^^^^^^

SynTool can be installed by the following steps:

.. code-block:: bash

    # install miniconda
    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
    bash Miniconda3-latest-Linux-x86_64.sh

    # create a new environment and poetry
    conda create -n syntool -c conda-forge "poetry=1.3.2" "python=3.10" -y
    conda activate syntool

    # clone SynTool
    git clone https://github.com/Laboratoire-de-Chemoinformatique/Syntool.git

    # navigate to the SynTool folder and install all the dependencies
    cd SynTool/
    poetry install --with gpu
    conda activate syntool

If Poetry fails with error, a possible solution is to update the bashrc file with the following command:

.. code-block:: bash

    echo 'export PYTHON_KEYRING_BACKEND=keyring.backends.null.Keyring' >> ~/.bashrc
    exec "bash"

After installation, one can add the ``syntool`` environment in their Jupyter platform:

.. code-block:: bash

    python -m ipykernel install --user --name syntool --display-name "syntool"

Quick start
------------

Each command in SynTool has a description that can be called with ``syntool --help`` and ``syntool command --help``

To run a retrosynthesis planning in SynTool the reaction rules, trained retrosynthetic models (policy network and value network),
and building block molecules are needed.

The planning command takes the file with the SMILES of target molecules listed one by one.
Also, the target molecule can be provided in the SDF format.

If you use your custom building blocks, be sure to canonicalize them before planning.

.. code-block:: bash

    # download planning data
    syntool download_planning_data

    # canonicalize building blocks
    syntool building_blocks --input building_blocks_custom.smi --output planning_data/building_blocks.smi

    # planning with rollout evaluation
    syntool planning --config configs/planning.yaml --targets targets.smi --reaction_rules planning_data/reaction_rules.pickle --building_blocks planning_data/building_blocks.smi --policy_network planning_data/ranking_policy_network.ckpt --results_dir planning_results

    # planning with value network evaluation
    syntool planning --config configs/planning.yaml --targets targets.smi --reaction_rules planning_data/reaction_rules.pickle --building_blocks planning_data/building_blocks.smi --policy_network planning_data/ranking_policy_network.ckpt --value_network planning_data/value_network.ckpt --results_dir planning_results

After retrosynthesis planning is finished, the visualized retrosynthesis routes can be fund in the results folder (``planning_results/extracted_routes_html``).

SynTool includes the full pipeline of reaction data curation, reaction rules extraction, and retrosynthetic models training.
For more details consult the corresponding sections in the documentation `here <https://laboratoire-de-chemoinformatique.github.io/SynTool/>`_.

Tutorials
----------------------
SynTool can be accessed via the Python interface. For a better understanding of SynTool and its functionalities consult
the tutorials in `SynTool/tutorials`. Currently, two tutorials are available:

``tutorials/general_tutorial.ipynb`` – explains how to do a reaction rules extraction, policy network training, and retrosynthesis planning in SynTool.

``tutorials/planning_tutorial.ipynb`` – explains how to do a retrosynthesis planning with various configurations of planning algorithms (various expansion/evaluation functions and search strategies).


Graphical user interface
---------------------------

Retrosynthesis planning in SynTool is also available by the simple graphical user interface (GUI).

1. Create an account on HuggingFace: https://huggingface.co/join

2. Once created and logged in, join SynTool group: https://huggingface.co/organizations/SynTool/share/rWSFhgqKxsMBQbObqspfFpRpZeTZQUGrol

3. The GUI is then available on: https://huggingface.co/spaces/SynTool/SynTool_GUI

The current version of GUI now is under development.

Documentation
----------------------

The detailed documentation can be found `here <https://laboratoire-de-chemoinformatique.github.io/SynTool/>`_.

