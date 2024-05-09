.. _reaction_standardization:

Reaction standardization
===========================
This page explains how to do a reaction standardization in SynTool.

Introduction
-------------------------
The reaction data are standardized using an original protocol for reaction data curation
published earlier [https://doi.org/10.1002/minf.202100119]. This protocol includes two layers:
standardization of individual molecules (reactants, reagents, products) and reaction standardization.
Steps for standardization of individual molecules include functional group standardization, aromatization/kekulization,
valence checking, hydrogens manipulation, cleaning isotopes, and radicals, etc.
The reaction standardization layer includes reaction role assignment, reaction equation balancing,
and atom-to-atom mapping fixing. The duplicate reactions and erroneous reactions are removed.

This protocol includes several steps such as:

    * transform functional groups, kekulize
    * check for radicals, isotopes, regroup ions
    * check valences
    * aromatize
    * fix mapping (for symmetric functional groups)
    * remove unchanged parts of the reaction, explicit hydrogens
    * remove reaction duplicates

Configuration
---------------------------
Reaction data standardization can be adjusted with the bellow configuration yaml file (these default parameters are recommended).

.. code-block:: yaml

    ignore_mapping: True
    skip_errors: True
    keep_unbalanced_ions: False
    keep_reagents: False
    action_on_isotopes: False

**Configuration parameters**:

.. table::
    :widths: 30 10 50

    ================================== ======= =========================================================================
    Parameter                          Default  Description
    ================================== ======= =========================================================================
    ignore_mapping                     True    If True, will ignore the original mapping in the file
    skip_errors                        True    If True, will ignore some errors during the reaction processes
    keep_unbalanced_ions               False   If True, will keep reactions with unbalanced ions
    keep_reagents                      False   If True, will keep reagents from the reactions
    action_on_isotopes                 False   If True, will ignore reactions with isotopes
    ================================== ======= =========================================================================

CLI
---------------------------
Reaction standardization can be performed with the below command.

.. code-block:: bash

    syntool reaction_standardizing --config standardization.yaml --input reaction_data_mapped.smi --output reaction_data_standardized.smi

**Parameters**:
    - ``config`` - the path to the configuration file.
    - ``input`` - the path to the file (.smi or .rdf) with reactions to be standardized.
    - ``output`` - the path to the file (.smi or .rdf) where standardized reactions will be stored.

The extension of the input/output files will be automatically parsed.