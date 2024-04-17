.. _data_download:

Data download
===========================

This page explains how to download data for retrosythetic models training and retrosynthesis planning in SynTool.

Introduction
---------------------------
For the training of the retrosynthetic models (policy and value network, reaction rules) the following types of data are needed:

    - Reaction data – needed for reaction rules extraction and ranking policy network training.
    - Molecule data – needed for filtering policy network training.
    - Targets data – needed for value network training (targets for planning simulation in reinforcement-based tuning).
    - Building blocks - needed for retrosynthesis planning simulations in reinforcement-based value network tuning.

For the retrosynthesis planning the following data and files are needed:

    - Trained retrosynthetic models – already trained policy and value networks can be used in retrosynthesis planning.
    - Reaction rules
    - Building blocks

As a source of reaction and molecule data public database are used such as USPTO, ChEMBL, COCONUT.

Configuration
---------------------------
Data download does not require any special configuration in the current version of SynTool.

CLI
---------------------------
Data download can be performed with the below commands.

**Data download for retrosynthetic models training**

.. code-block:: bash

    syntool download_training_data --root_dir training_data

**Parameters**:
    - `root_dir` - the path to the directory where the data files will be stored.

**Data download for retrosythesis planning**

.. code-block:: bash

    syntool download_planning_data --root_dir training_data

**Parameters**:
    - `root_dir` - the path to the directory where the data files will be stored.
