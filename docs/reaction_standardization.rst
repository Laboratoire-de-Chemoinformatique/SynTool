.. _reaction_standardization:

Reaction standardization
===========================
This page explains how to do a reaction standardization in SynTool.

Introduction
-------------------------
The reaction data are standardized using an original protocol for reaction data curation
published earlier [https://doi.org/10.1002/minf.202100119].

This protocol includes several steps such as:
    * transform functional groups, kekulize
    * check for radicals (remove if something was found), isotopes, regroup ions
    * check valences (remove if something is wrong)
    * aromatize (thiele method)
    * fix mapping (for symmetric functional groups) if such is in
    * remove unchanged parts, explicit hydrogens
    * remove reaction duplicate

Configuration
---------------------------
Reaction data standardization can be adjusted with the bellow configuration yaml file (these default parameters are recommended).

.. code-block:: yaml

    ignore_mapping: True
    skip_errors: True
    keep_unbalanced_ions: False
    keep_reagents: False
    action_on_isotopes: True

**Configuration parameters**:

    - `ignore_mapping` - if True, will ignore the original mapping in the file.
    - `skip_errors` - if True, will ignore some errors during the reaction processes.
    - `keep_unbalanced_ions` - if True, will keep reactions with unbalanced ions.
    - `keep_reagents` - if True, will keep reagents from the reactions.
    - `action_on_isotopes` - if True, will ignore reactions with isotopes.

CLI
---------------------------
Reaction standardization can be performed with the below command.

.. code-block:: bash

    syntool reaction_standardizing --config standardization.yaml --input reaction_data_mapped.smi --output reaction_data_standardized.smi

**Parameters**:
    - `config` - the path to the configuration file.
    - `input` - the path to the file (.smi or .rdf) with reactions to be standardized.
    - `output` - the path to the file (.smi or .rdf) where standardized reactions will be stored.

The extension of the input/output files will be automatically parsed.