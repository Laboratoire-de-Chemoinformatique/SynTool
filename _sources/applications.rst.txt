
SynTool applications
===========================
This page shows some usage cases of SynTool, potentially useful in reaction informatics and Computer-Aided Synthesis Planning (CASP).

Usage cases
---------------------------

**1. Curating/cleaning reaction data**

SynTool provides original reaction data curation protocols (atom mapping, standardization, and filtration),
which can be used separately and independently. This curated data can be used in other applications or CASP tools.

See the details in :ref:`reaction_standardization` and :ref:`reaction_filtration`.

**2. Building custom retrosynthesis planners**

SynTool incorporates the full pipeline of preparation of retrosynthetic models and building ready-to-use retrosynthesis planners.
This allows for the usage of SynTool in retrosynthesis planning based on custom and private reaction data, specific reaction databases,
or specific types of chemistry. With SynTool it is possible easily to build a private planner from any reaction data sources.

See the details in :ref:`index`.

**3. Extracting reaction rules from the reaction database**

SynTool incorporates the original module for reaction rule extraction from reaction data.
The protocol of reaction rule extraction is flexible and allows balancing between the generality and specificity of reaction rules
depending on the task. The extracted reaction rules can be stored as reaction SMARTS and currently are compatible with the AiZynthFinder tool.

See the details in :ref:`reaction_rules_extraction`.

**4. Retrosynthesis planning with custom reaction rules**

In SynTool it is possible to train a filtering policy network for the prediction of applicable reaction rules in tree search.
The distinctive feature of the filtering policy network is that it can be trained with an external set of reaction rules,
extracted by other software, and created manually. Then, these reaction rules and trained policy can be used in advanced planning algorithms in SynTool.

See the details in :ref:`policy_network`.

**5. Advanced planning algorithms**

The flexibility of SynTool and a collection of complementary neural networks in SynTool allows for advanced retrosynthesis planning,
which sometimes may find the solution for some target molecules unsolved by default planning in SynTool or other tools.
Advanced planning is slower than other counterparts but is more powerful because of a more comprehensive exploration of the search tree.

See the details in :ref:`retrosynthesis_planning`.
