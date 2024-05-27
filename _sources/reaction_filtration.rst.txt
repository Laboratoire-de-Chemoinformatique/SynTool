.. _reaction_filtration:

Reaction filtration
===========================
This page explains how to do a reaction filtration in SynTool.

Introduction
---------------------------
Reaction filtration is a crucial step in reaction data curation. It ensures the validity of reactions
used for reaction rule extraction. The current version of SynTool includes 11 reaction filters (see below).
In brackets, it is shown how this filter should be listed in the configuration file to be activated.

The current available reaction filters in SynTool:

.. table::
    :widths: 35 50

    ================================== =================================================================================
    Reaction filter                    Description
    ================================== =================================================================================
    compete_products_config            Checks if there are compete reactions
    dynamic_bonds_config               Checks if there is an unacceptable number of dynamic bonds in CGR
    small_molecules_config             Checks if there are only small molecules in the reaction or if there is only one small reactant or product
    cgr_connected_components_config    Checks if CGR contains unrelated components (without reagents)
    rings_change_config                Checks if there is changing rings number in the reaction
    strange_carbons_config             Checks if there are 'strange' carbons in the reaction
    no_reaction_config                 Checks if there is no reaction in the provided reaction container
    multi_center_config                Checks if there is a multicenter reaction
    wrong_ch_breaking_config           Checks for incorrect C-C bond formation from breaking a C-H bond
    cc_sp3_breaking_config             Checks if there is C(sp3)-C bond breaking
    cc_ring_breaking_config            Checks if a reaction involves ring C-C bond breaking
    ================================== =================================================================================

Configuration
---------------------------
The current recommendation is to divide these filters into two groups (standard filters and standard + special filters),
which can be set up by configuration yaml files (these default parameters are recommended).

Standard filters (4 filters):

.. code-block:: yaml

    multi_center_config:
    no_reaction_config:
    dynamic_bonds_config:
      min_bonds_number: 1
      max_bonds_number: 6
    small_molecules_config:
      limit: 6

Standard and special filters (4 + 3 filters):

.. code-block:: yaml

    multi_center_config:
    no_reaction_config:
    dynamic_bonds_config:
      min_bonds_number: 1
      max_bonds_number: 6
    small_molecules_config:
      limit: 6
    cc_ring_breaking_config:
    wrong_ch_breaking_config:
    cc_sp3_breaking_config:

**Important-1:** if the reaction filter name is listed in the configuration file (see above), it means that this filter will be activated. Also, some filters requires additional parameters (e.g. ``small_molecules_config``).

**Important-2:** the order of filters listed in the configuration file defines the order of their application to the input reactions.

CLI
---------------------------
Reaction filtration can be performed with the below command.

.. code-block:: bash

    syntool reaction_filtering --config filtration.yaml --input reaction_data_standardized.smi --output reaction_data_filtered.smi

**Parameters**:
    - ``config`` - the path to the configuration file.
    - ``input`` - the path to the file (.smi or .rdf) with reactions to be filtered.
    - ``output`` - the path to the file (.smi or .rdf) where filtered reactions to be stored.

The extension of the input/output files will be automatically parsed.