.. _reaction_mapping:

Reaction mapping
===========================
This page explains how to do a reaction mapping in SynTool.

Introduction
---------------------------
Reaction atom-to-atom (AAM) mapping in SynTool is performed with GraphormerMapper, a new algorithm for AAM based on a transformer
neural network adopted for the direct processing of molecular graphs as sets of atoms and bonds, as opposed to SMILES/SELFIES
sequence-based approaches, in combination with the Bidirectional Encoder Representations from Transformers (BERT) network.
The graph transformer serves to extract molecular features that are tied to atoms and bonds. The BERT network is used for
chemical transformation learning. In a benchmarking study, it was demonstrated [https://doi.org/10.1021/acs.jcim.2c00344]
that GraphormerMapper is superior to the state-of-the-art IBM RxnMapper algorithm in the “Golden” benchmarking data set
(total correctly mapped reactions 89.5% vs. 84.5%).

Configuration
---------------------------
Reaction mapping does not require any special configuration in the current version of SynTool.

CLI
---------------------------
Reaction mapping can be performed with the below command.

.. code-block:: bash

    syntool reaction_mapping --input reaction_data_init.smi --output reaction_data_mapped.smi

**Parameters**:
    - ``input`` - the path to the file (.smi only) with reactions to be mapped.
    - ``output`` - the path to the file (.smi or .rdf) where mapped reactions will be stored.

**Important:** Currently only .smi input file format is accepted.

