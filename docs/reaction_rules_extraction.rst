.. _reaction_rules_extraction:

Reaction rules extraction
===========================

This page explains how to do a reaction rules extraction in SynTool.

Introduction
---------------------------
The protocol for extraction of reaction rules from reactions in SynTool involves the following steps:

    1. The atom-to-atom mapping (AAM) in reaction must be established
    2. Each atom in the reaction is labeled with set of properties such as hybridization, the number of neighbors, the charge, and the ring sizes in which the atoms participate.
    3. Based on the reaction AAM, the atoms of reactants that change their properties in products are included to the reaction center of the reaction

A reaction rule extracted by this protocol is applied to the product of the original reaction. If it successfully
generates the reactants of the reaction, the reaction rule is considered valid.

Configuration
---------------------------

The reaction rules extraction protocol can be adjusted with the configuration yaml file:

.. code-block:: yaml

    environment_atom_count: 1
    min_popularity: 3
    multicenter_rules: True
    as_query_container: True
    reverse_rule: True
    reactor_validation: True
    include_func_groups: False
    func_groups_list:
    include_rings: False
    keep_leaving_groups: False
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
        neighbors: False
        hybridization: False
        implicit_hydrogens: False
        ring_sizes: False

**Configuration parameters**:

.. table::
    :widths: 30 10 50

    ================================== ======= =========================================================================
    Parameter                          Default  Description
    ================================== ======= =========================================================================
    multicenter_rules                  True    Determines whether a single rule is extracted for all centers in multicenter reactions (True) or if separate rules are generated for each center (False).
    as_query_container                 True    When set to True, the extracted rules are formatted as QueryContainer objects, similar to SMARTS for chemical pattern matching.
    reverse_rule                       True    If True, the direction of the reaction is reversed during rule extraction, which is useful for retrosynthesis.
    reactor_validation                 True    Activates the validation of each generated rule in a chemical reactor to confirm the accurate generation of products from reactants when set to True.
    include_func_groups                False   If True, specific functional groups are included in the reaction rule in addition to the reaction center and its environment.
    func_groups_list                   []      Specifies a list of functional groups to be included when include_func_groups is True.
    include_rings                      False   Includes ring structures in the reaction rules connected to the reaction center atoms if set to True.
    keep_leaving_groups                False   Keeps the leaving groups in the extracted reaction rule when set to True. The default is False.
    keep_incoming_groups               False   Retains incoming groups in the extracted reaction rule if set to True. The default is False.
    keep_reagents                      False   Includes reagents in the extracted reaction rule when True. The default is False.
    environment_atom_count             1       Determines the number of layers of atoms around the reaction center to be included in the reaction rule. A value of 0 includes only the reaction center, 1 includes the first surrounding layer, and so on.
    min_popularity                     3       Determines the minimum number of occurrences of a reaction rule in the reaction dataset. The default is 3.
    keep_metadata                      False   Preserves associated metadata with the reaction in the extracted rule when set to True. The default is False.
    single_reactant_only               True    Limits the extracted reaction rules to those with only a single reactant molecule if True. The default is True.
    atom_info_retention                --      Dictates the level of detail retained about atoms in the reaction center and their environment. Default settings retain information about neighbors, hybridization, implicit hydrogens, and ring sizes for both the reaction center and its environment.
    ================================== ======= =========================================================================

CLI
---------------------------
Reaction rules extraction can be performed with the below command.

.. code-block:: bash

    syntool rule_extracting --config extraction.yaml --input reaction_data_filtered.smi --output reaction_rules.pickle

**Parameters**:
    - ``config`` - the path to the configuration file.
    - ``input`` - the path to the file (.smi or .rdf) with reactions to be standardized.
    - ``output`` - the path to the file (.pickle) where extracted reactions rules will be stored.

The extension of the input/output files will be automatically parsed.


