.. _reaction_rules_extraction:

Reaction rules extraction
===========================

This page explains how to do a reaction rules extraction in SynTool.

Introduction
---------------------------
The protocol for extraction of reaction rules from reactions in SynTool involves the following steps:

    * Substructure Extraction - for each reactant and product in a given reaction, substructures containing the atoms of the reaction center and their immediate environment are extracted.
    * Substructure Exchange -the reactant and product substructures are then exchanged.
    * Reagents Handling - if the reaction includes reagents, they are not incorporated into the retro-rule.
    * Label Preservation - all labels related to the atoms of the reaction center, such as hybridization, the number of neighbors, and the ring sizes in which the atoms participate, are preserved. For atoms in the first environment, only the sizes of rings are preserved.

A reaction rule extracted by this protocol is applied to the product of the original reaction. If it successfully
generates the reactants of the reaction, the reaction rule is considered valid.

Configuration
---------------------------

The reaction rules extraction protocol can be adjusted with the configuration file:

.. code-block:: yaml

    environment_atom_count: 1
    min_popularity: 3
    multicenter_rules: True
    as_query_container: True
    reverse_rule: True
    include_func_groups: False
    func_groups_list:
    include_rings: False
    keep_leaving_groups: True
    keep_incoming_groups: False
    keep_reagents: False
    keep_metadata: False
    single_reactant_only: True
    atom_info_retention:
      reaction_center:
        neighbors: True
        hybridization: True
        implicit_hydrogens: False
        ring_sizes: False
      environment:
        neighbors: True
        hybridization: False
        implicit_hydrogens: False
        ring_sizes: False

**Configuration parameters**:

    - `multicenter_rules` - determines whether a single rule is extracted for all centers in multicenter reactions (True) or if separate rules are generated for each center (False). The default is True.
    - `as_query_container` - when set to True, the extracted rules are formatted as QueryContainer objects, similar to SMARTS for chemical pattern matching. The default is True.
    - `reverse_rule` - if True, the direction of the reaction is reversed during rule extraction, which is useful for retrosynthesis. The default is True.
    - `reactor_validation` - activates the validation of each generated rule in a chemical reactor to confirm the accurate generation of products from reactants when set to True. The default is True.
    - `include_func_groups` - if True, specific functional groups are included in the reaction rule in addition to the reaction center and its environment. The default is False.
    - `func_groups_list` - specifies a list of functional groups to be included when include_func_groups is True.
    - `include_rings` - includes ring structures in the reaction rules connected to the reaction center atoms if set to True. The default is False.
    - `keep_leaving_groups` - keeps the leaving groups in the extracted reaction rule when set to True. The default is False.
    - `keep_incoming_groups` - retains incoming groups in the extracted reaction rule if set to True. The default is False.
    - `keep_reagents` - includes reagents in the extracted reaction rule when True. The default is False.
    - `environment_atom_count` - sets the number of layers of atoms around the reaction center to be included in the rule. A value of 0 includes only the reaction center, 1 includes the first surrounding layer, and so on. The default is 1.
    - `min_popularity` - establishes the minimum number of times a rule must be applied to be included in further analysis. The default is 3.
    - `keep_metadata` - preserves associated metadata with the reaction in the extracted rule when set to True. The default is False.
    - `single_reactant_only` - limits the extracted rules to those with only a single reactant molecule if True. The default is True.
    - `atom_info_retention` - dictates the level of detail retained about atoms in the reaction center and their environment. Default settings retain information about neighbors, hybridization, implicit hydrogens, and ring sizes for both the reaction center and its environment.

CLI
---------------------------
Reaction rules extraction can be performed with the below command.

.. code-block:: bash

    syntool rule_extracting --config extraction.yaml --input reaction_data_filtered.smi --output reaction_rules.pickle

**Parameters**:
    - `config` - the path to the configuration file.
    - `input` - the path to the file (.smi or .rdf) with reactions to be standardized.
    - `output` - the path to the file (.pickle) where extracted reactions rules will be stored.

The extension of the input/output files will be automatically parsed.


