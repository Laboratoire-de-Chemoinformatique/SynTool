
SynTool contribution
===========================
This page explains possible ways of contributing to SynTool, its improvement, and extension.

SynTool extension
---------------------------

**1. Adding new reaction/molecule standardizers**

The quality of reaction data is crucial in training retrosynthetic models and retrosynthesis planning.
The current protocol of reaction data curation can be extended by the addition of new reaction standardizers
and customized depending on the task.

**2. Adding new reaction filters**

The quality of reaction data is crucial in training retrosynthetic models and retrosynthesis planning.
The current protocol of reaction data curation can be extended by the addition of new reaction filters and customized depending on the task.

**3. Adding new expansion policies**

Expansion policy in tree search can prioritize some reaction rules navigating the search and defining
the final patterns in predicted retrosynthetic routes. Thus, expansion policy is an interface between algorithmic search
and the chemical context of panning. The addition of specialized expansion policies can customize
the general design of predicted retrosynthetic routes depending on the task.
