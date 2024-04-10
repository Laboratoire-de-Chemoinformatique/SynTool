User guide
================

This page lists some practical recommendations about using SynTool for data curation, retrosynthetic models training and retrosynthesis planning.

Basic recommendations
---------------------------

**1. Reaction data filtration - 1**

*Always do reaction data filtration.*

Reaction data filtration is a crucial step in reaction data curation pipeline. Reaction filtration ensures the correctness of the extracted reaction rules
and is needed for correct execution of the programming code (some erroneous reactions may crash the current version of the SynTool code).
Thus, it is recommended to do a reaction data filtration before the extraction of reaction rules and training retrosynthetic models.

**2. Reaction data filtration - 2**

*Input and output reaction representation may be different after filtration*

The current version of reaction data filtration protocol in SynTool include some function for additional standardization of input reactons.
This is why sometimes the output reaction SMILES, after it passed all the filters, may not exactly to the input reaction SMILES.

**3. Data curation parallelization**

*Do not use more than 4-8 CPU*

The current version of SynTool is not perfectly optimal in terms of memory usage with many CPUs (this problem will be fixed in future versions).
This is why it is recommended to set no more than 4 CPU for steps related to the data curation.

**4. Search strategies in retrosynthesis planning**

*"Evaluation first" search strategy is not compatible with the rollout evaluation.*

In SynTool, there are two main search strategies implemented - "Expansion first" and "Evaluation first" strategy.
These are the strategies for navigating the search tree. "Expansion first" prioritizes the expansion of new nodes and
assigns to each new node the default value. "Evaluation first" prioritizes the evaluation of each new node first.
Notice, that the usage of "Evaluation first" strategy with the current implementation of rollout function in SynTool is
not reasonable in terms of the total search time because of time-consuming execution of the rollout function. Also, the
current implementation of the rollout function may mislead the search in case of "Evaluation first" strategy do tue the limited
explanation of the tree in rollout simulations. Therefore, the current recommendation is to use "Evaluation first" strategy with
value network evaluation only.