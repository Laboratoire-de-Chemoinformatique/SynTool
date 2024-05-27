.. _reaction_standardization:

Reaction standardization
===========================
This page explains how to do a reaction standardization in SynTool.

Introduction
-------------------------
**Reaction atom mapping**. Reaction atom-to-atom (AAM) mapping in SynTool is performed with GraphormerMapper,
a new algorithm for AAM based on a transformerneural network adopted for the direct processing of molecular graphs
as sets of atoms and bonds, as opposed to SMILES/SELFIES sequence-based approaches, in combination with the
Bidirectional Encoder Representations from Transformers (BERT) network. The graph transformer serves to extract molecular
features that are tied to atoms and bonds. The BERT network is used for chemical transformation learning.
In a benchmarking study, it was demonstrated [https://doi.org/10.1021/acs.jcim.2c00344] that GraphormerMapper
is superior to the state-of-the-art IBM RxnMapper algorithm in the “Golden” benchmarking data set
(total correctly mapped reactions 89.5% vs. 84.5%).

**Reaction standardization**. The reaction data are standardized using an original protocol for reaction data curation
published earlier [https://doi.org/10.1002/minf.202100119]. This protocol includes two layers:
standardization of individual molecules (reactants, reagents, products) and reaction standardization.
Steps for standardization of individual molecules include functional group standardization, aromatization/kekulization,
valence checking, hydrogens manipulation, cleaning isotopes, and radicals, etc.
The reaction standardization layer includes reaction role assignment, reaction equation balancing,
and atom-to-atom mapping fixing. The duplicate reactions and erroneous reactions are removed.

The current available reaction standardizers in SynTool:

.. table::
    :widths: 30 50

    ================================== =================================================================================
    Reaction standardizer              Description
    ================================== =================================================================================
    reaction_mapping_config            Maps atoms of the reaction using chython (chytorch)
    functional_groups_config           Standardization of functional groups
    kekule_form_config                 Transform molecules to Kekule form when possible
    check_valence_config               Check atom valences
    implicify_hydrogens_config         Remove hydrogen atoms
    check_isotopes_config              Check and clean isotope atoms when possible
    split_ions_config                  Split ions in reaction when possible
    aromatic_form_config               Transform molecules to aromatic form when possible
    mapping_fix_config                 Fix atom-to-atom mapping in reaction when needed and possible
    unchanged_parts_config             Remove unchanged parts in reaction
    small_molecules_config             Remove small molecule from reaction
    remove_reagents_config             Remove reagents from reaction
    rebalance_reaction_config          Rebalance reaction
    duplicate_reaction_config          Remove duplicate reactions
    ================================== =================================================================================


Configuration
---------------------------
Reaction standardization protocol can be adjusted configuration yaml file (these default parameters bellow are recommended).

.. code-block:: yaml

    reaction_mapping_config:
    functional_groups_config:
    kekule_form_config:
    check_valence_config:
    implicify_hydrogens_config:
    check_isotopes_config:
    split_ions_config:
    aromatic_form_config:
    mapping_fix_config:
    unchanged_parts_config:
    duplicate_reaction_config:

**Important-1:** if the reaction standardizer name is listed in the configuration file (see above), it means that this filter will be activated.

**Important-2:** the order of standardizers listed in the configuration file defines the order of their application to the input reactions.

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