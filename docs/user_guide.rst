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

*Input and output reaction representation may be different after filtration.*

The current version of reaction data filtration protocol in SynTool include some function for additional standardization of input reactons.
This is why sometimes the output reaction SMILES, after it passed all the filters, may not exactly to the input reaction SMILES.

**3. Data curation parallelization**

*Do not use more than 4-8 CPU.*

The current version of SynTool is not perfectly optimal in terms of memory usage with many CPUs (this problem will be fixed in future versions).
This is why it is recommended to set no more than 4 CPU for steps related to the data curation.

**4. Ranking and filtering policy networks -1 **

*Prefer ranking policy network over filtering policy network.*

The filtering policy network in its current implementation requires a lot of computational resources and its training is
practically feasible with > 30 CPUs and several dozen GB of RAM. The bottleneck of the current implementation is the preparation
of the training dataset, particularly the generation of binary vectors if successfully applied reaction rules to each training
molecule – on average, this step takes about 1.6 sec for one molecule (for around 10k reaction rules). Thus, with limited computational
resources, it is recommended to use a ranking policy network.

**5. Ranking and filtering policy networks -2 **

*Use filtering policy network for portability of reaction rules between different tools.*

Filtering policy networks can be trained with any set of reaction rules, including those generated with
other software because filtering network training does not depend on the original reaction dataset
from which the reaction rules were extracted. In this case, filtering policy network can be used
for comparison of reaction rules set extracted with different tools.

**6. Tree search in retrosynthesis planning - 1**

*"Evaluation first" search strategy is not compatible with the rollout evaluation.*

In SynTool, there are two main search strategies implemented - "Expansion first" and "Evaluation first" strategy.
These are the strategies for navigating the search tree. "Expansion first" prioritizes the expansion of new nodes and
assigns to each new node the default value. "Evaluation first" prioritizes the evaluation of each new node first.
Notice, that the usage of "Evaluation first" strategy with the current implementation of rollout function in SynTool is
not reasonable in terms of the total search time because of time-consuming execution of the rollout function. Also, the
current implementation of the rollout function may mislead the search in case of "Evaluation first" strategy do tue the limited
explanation of the tree in rollout simulations. Therefore, the current recommendation is to use "Evaluation first" strategy with
value network evaluation only.

**7. Tree search in retrosynthesis planning - 2**

*Try more search iterations with complex molecules, a limited set of reaction rules, or building blocks.*

Some target molecules (usually more complex and bigger molecules) require longer tree searches to be successfully
solved and may require longer retrosynthesis routes. The same is true, if there is only a mall set of reaction rules
or building blocks, which again requires for longer analysis to find the proper combination of reaction rules leading
to the limited amount of building blocks. In these cases, the increase in the number of search iterations may help to
find the successful retrosynthesis route for the given molecule.

**8. Tree search in retrosynthesis planning - 3**

*Currently retrosynthesis planning results in many similar retrosynthesis routes.*

Currently, there is no implementation of the retrosynthesis routes clustering in SynTool. It may lead to the generation
of many similar retrosynthesis routes for the target molecule.