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

This current default protocol includes several steps such as:

    1. Standardization of functional groups
    2. Transform molecules to Kekule form when possible
    3. Check atom valences
    4. Remove hydrogen atoms
    5. Check and clean isotope atoms when possible
    6. Split ions in reaction when possible
    7. Transform molecules to aromatic form when possible
    8. Fix atom-to-atom mapping in reaction when needed and possible
    9. Remove unchanged parts in reaction
    10. Remove duplicate reactions

Configuration
---------------------------
Reaction standardization does not require any special configuration in the current version of SynTool.

CLI
---------------------------
Reaction standardization can be performed with the below command.

.. code-block:: bash

    syntool reaction_standardizing --input reaction_data_mapped.smi --output reaction_data_standardized.smi

**Parameters**:
    - ``input`` - the path to the file (.smi or .rdf) with reactions to be standardized.
    - ``output`` - the path to the file (.smi or .rdf) where standardized reactions will be stored.

The extension of the input/output files will be automatically parsed.