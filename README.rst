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
Here are some implemented commands:

* syntool_planning
* syntool_training

Each command has a description that can be called with ``command --help``

Run retrosynthetic planning
^^^^^^^^^^^
.. code-block:: bash

    syntool_planning_data
    syntool_planning --config="planning_config.yaml"

Run training from scratch
^^^^^^^^^^^
.. code-block:: bash

    syntool_training_data
    syntool_training --config="training_config.yaml"


Documentation
-----------

The detailed documentation can be found `here <https://laboratoire-de-chemoinformatique.github.io/Syntool/>`_

Tests
-----------

.. code-block:: bash

    syntool_training --config="configs/training_config.yaml"
    syntool_planning --config="configs/planning_config.yaml"
