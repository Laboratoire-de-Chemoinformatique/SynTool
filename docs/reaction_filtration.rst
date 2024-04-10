Reaction filtration
===========================
This page explains how to do a reaction filtration in SynTool.

Introduction
---------------------------
Reaction filtration is a crucial step in reaction data curation. It ensures the correctness of reactions
used fo reaction rules extraction. The current version of SynTool includes 11 reaction filters (see below).
In brackets it is showed how this filter should be listed in the configuration file to be activated.

The current available filters in SynTool:

    * `CompeteProductsChecker` (`compete_products_config`) - checks if there are compete reactions.
    * `DynamicBondsChecker` (`dynamic_bonds_config`) - checks if there is an unacceptable number of dynamic bonds in CGR.
    * `SmallMoleculesChecker` (`small_molecules_config`) - checks if there are only small molecules in the reaction or if there is only one small reactant or product.
    * `CGRConnectedComponentsChecker` (`cgr_connected_components_config`) - checks if CGR contains unrelated components (without reagents).
    * `RingsChangeChecker` (`rings_change_config`) - checks if there is changing rings number in the reaction.
    * `StrangeCarbonsChecker` (`strange_carbons_config`) - checks if there are 'strange' carbons in the reaction.
    * `NoReactionChecker` (`no_reaction_config`) - checks if there is no reaction in the provided reaction container.
    * `MultiCenterChecker` (`multi_center_config`) - checks if there is a multicenter reaction.
    * `WrongCHBreakingChecker` (`wrong_ch_breaking_config`) - checks for incorrect C-C bond formation from breaking a C-H bond.
    * `CCsp3BreakingChecker` (`cc_sp3_breaking_config`) - checks if there is C(sp3)-C bond breaking.
    * `CCRingBreakingChecker` (`cc_ring_breaking_config`) - checks if a reaction involves ring C-C bond breaking.

Configuration
---------------------------
The current recommendation is to divide these filters into two groups (standard filters and standard + special filters),
which can be set up by configuration files (these default parameters are recommended).

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

**Important**: ih the reaction filter name is listed in the configuration file (see above), it means that this filter will be activated.
Also, some filters requires additional parameters (e.g. `small_molecules_config`).

CLI
---------------------------
Reaction filtration can be performed with the below command.

.. code-block:: bash

    syntool reaction_filtering --config filtration.yaml --input reaction_data_standardized.smi --output reaction_data_filtered.smi

**Parameters**:
    - `--config` is the path to the configuration file.
    - `--input` is the path to the file (.smi or .rdf) with reactions to be filtered.
    - `--output` is the path to the file (.smi or .rdf) where filtered reactions to be stored.

The extension of the files will be automatically parsed and for reading/writing reactions.