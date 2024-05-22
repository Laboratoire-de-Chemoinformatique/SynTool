"""Module containing classes and functions for reactions standardizing.

This module contains the open-source code from
https://github.com/Laboratoire-de-Chemoinformatique/Reaction_Data_Cleaning/blob/master/scripts/standardizer.py
"""

import logging
from io import TextIOWrapper
from typing import Dict, List, Tuple

import ray
from CGRtools.containers import MoleculeContainer, ReactionContainer
from tqdm import tqdm

from SynTool.chem.utils import (rebalance_reaction, remove_reagents,
                                remove_small_molecules)
from SynTool.utils.files import ReactionReader, ReactionWriter
from SynTool.utils.logging import GeneralException, HiddenPrints


class FunctionalGroupsStandardizer:
    """Functional groups standardization."""

    def __call__(self, reaction: ReactionContainer) -> ReactionContainer | None:
        """Functional groups standardization.

        :param reaction: Input reaction.
        :return: Returns standardized reaction if the reaction has standardized
            successfully, else None.
        """
        try:
            reaction.standardize()
            return reaction
        except GeneralException:
            return None


class KekuleFormStandardizer:
    """Reactants/reagents/products kekulization."""

    def __call__(self, reaction: ReactionContainer) -> ReactionContainer | None:
        """Reactants/reagents/products kekulization.

        :param reaction: Input reaction.
        :return: Returns standardized reaction if the reaction has standardized
            successfully, else None.
        """
        try:
            reaction.kekule()
            return reaction
        except GeneralException:
            return None


class CheckValenceStandardizer:
    """Check valence."""

    def __call__(self, reaction: ReactionContainer) -> ReactionContainer | None:
        """Check valence.

        :param reaction: Input reaction.
        :return: Returns reaction if the atom valences are correct, else None.
        """
        for molecule in reaction.reactants + reaction.products + reaction.reagents:
            valence_mistakes = molecule.check_valence()
            if valence_mistakes:
                return None
        return reaction


class ImplicifyHydrogensStandardizer:
    """Implicify hydrogens."""

    def __call__(self, reaction: ReactionContainer) -> ReactionContainer | None:
        """Implicify hydrogens.

        :param reaction: Input reaction.
        :return: Returns reaction with removed hydrogens, else None.
        """
        try:
            reaction.implicify_hydrogens()
            return reaction
        except GeneralException:
            return None


class CheckIsotopesStandardizer:
    """Check isotopes."""

    def __call__(self, reaction: ReactionContainer) -> ReactionContainer | None:
        """Check isotopes.

        :param reaction: Input reaction.
        :return: Returns reaction with cleaned isotopes, else None.
        """
        is_isotope = False
        for molecule in reaction.reactants + reaction.products:
            for _, atom in molecule.atoms():
                if atom.isotope:
                    is_isotope = True

        if is_isotope:
            reaction.clean_isotopes()

        return reaction


class SplitIonsStandardizer:
    """Computing charge of molecule."""

    def _calc_charge(self, molecule: MoleculeContainer) -> int:
        """Computing charge of molecule.

        :param molecule: Input reactant/reagent/product.
        :return: The total charge of the molecule.
        """
        return sum(molecule._charges.values())

    def _split_ions(self, reaction: ReactionContainer):
        """Split ions in a reaction.

        :param reaction: Input reaction.
        :return: A tuple with the corresponding reaction and
        a return code as int (0 - nothing was changed, 1 - ions were split, 2 - ions were split but the reaction
        is imbalanced).
        """
        meta = reaction.meta
        reaction_parts = []
        return_codes = []
        for molecules in (reaction.reactants, reaction.reagents, reaction.products):
            divided_molecules = [x for m in molecules for x in m.split(".")]

            total_charge = 0
            ions_present = False
            for molecule in divided_molecules:
                mol_charge = self._calc_charge(molecule)
                total_charge += mol_charge
                if mol_charge != 0:
                    ions_present = True

            if ions_present and total_charge:
                return_codes.append(2)
            elif ions_present:
                return_codes.append(1)
            else:
                return_codes.append(0)

            reaction_parts.append(tuple(divided_molecules))

        return ReactionContainer(
            reactants=reaction_parts[0],
            reagents=reaction_parts[1],
            products=reaction_parts[2],
            meta=meta,
        ), max(return_codes)

    def __call__(self, reaction: ReactionContainer) -> ReactionContainer | None:
        """Split ions.

        :param reaction: Input reaction.
        :return: Returns reaction with split ions, else None.
        """
        try:
            reaction, return_code = self._split_ions(reaction)
            if return_code in [0, 1]:  # ions were split
                return reaction
            if return_code == 2:  # ions were split but the reaction is imbalanced
                return None
        except GeneralException:
            return None


class AromaticFormStandardizer:
    """Aromatize molecules in reaction."""

    def __call__(self, reaction: ReactionContainer) -> ReactionContainer | None:
        """Aromatize molecules in reaction.

        :param reaction: Input reaction.
        :return: Returns reaction with aromatized reactants/reagents/products, else
            None.
        """
        try:
            reaction.thiele()
            return reaction
        except GeneralException:
            return None


class MappingFixStandardizer:
    """Fix atom-to-atom mapping in reaction."""

    def __call__(self, reaction: ReactionContainer) -> ReactionContainer | None:
        """Fix atom-to-atom mapping in reaction.

        :param reaction: Input reaction.
        :return: Returns reaction with fixed atom-to-atom mapping, else None.
        """
        try:
            reaction.fix_mapping()
            return reaction
        except GeneralException:
            return None


class UnchangedPartsStandardizer:
    """Ungroup molecules, remove unchanged parts from reactants and products."""

    def __init__(
        self,
        add_reagents_to_reactants: bool = False,
        keep_reagents: bool = False,
    ):
        self.add_reagents_to_reactants = add_reagents_to_reactants
        self.keep_reagents = keep_reagents

    def _remove_unchanged_parts(self, reaction: ReactionContainer) -> ReactionContainer:
        """Ungroup molecules, remove unchanged parts from reactants and products.

        :param reaction: Input reaction.
        :return: Returns reaction with removed unchanged parts, else None.
        """
        meta = reaction.meta
        new_reactants = list(reaction.reactants)
        new_reagents = list(reaction.reagents)
        if self.add_reagents_to_reactants:
            new_reactants.extend(new_reagents)
            new_reagents = []
        reactants = new_reactants.copy()
        new_products = list(reaction.products)

        for reactant in reactants:
            if reactant in new_products:
                new_reagents.append(reactant)
                new_reactants.remove(reactant)
                new_products.remove(reactant)
        if not self.keep_reagents:
            new_reagents = []
        return ReactionContainer(
            reactants=tuple(new_reactants),
            reagents=tuple(new_reagents),
            products=tuple(new_products),
            meta=meta,
        )

    def __call__(self, reaction: ReactionContainer) -> ReactionContainer | None:
        """Ungroup molecules, remove unchanged parts from reactants and products.

        :param reaction: Input reaction.
        :return: Returns reaction with removed unchanged parts, else None.
        """
        try:
            reaction = self._remove_unchanged_parts(reaction)
            if not reaction.reactants and reaction.products:
                return None
            if not reaction.products and reaction.reactants:
                return None
            if not reaction.reactants and not reaction.products:
                return None
            return reaction
        except GeneralException:
            return None


class DuplicateReactionStandardizer:
    """Remove duplicate reactions."""

    def __init__(self):
        self.hash_set = set()

    def __call__(self, reaction: ReactionContainer) -> ReactionContainer | None:
        """Remove duplicate reactions.

        :param reaction: Input reaction.
        :return: Returns reaction if it is unique (not duplicate), else None
        """

        h = hash(reaction)
        if h not in self.hash_set:
            self.hash_set.add(h)
            return reaction

        return None


class SmallMoleculesStandardizer:
    """Remove small molecule from reaction."""

    def __init__(self, limit: int = 6):
        self.limit = limit

    def __call__(self, reaction: ReactionContainer) -> ReactionContainer | None:
        """Remove small molecule from reaction.

        :param reaction: Input reaction.
        :return: Returns reaction without small molecules, else None.
        """
        try:
            reaction = remove_small_molecules(reaction)
            return reaction
        except GeneralException:
            return None


class RemoveReagentsStandardizer:
    """Remove reagents from reaction."""

    def __init__(self, reagent_max_size: int = 7):
        self.reagent_max_size = reagent_max_size

    def __call__(self, reaction: ReactionContainer) -> ReactionContainer | None:
        """Remove reagents from reaction.

        :param reaction: Input reaction.
        :return: Returns reaction reagents, else None.
        """
        try:
            reaction = remove_reagents(
                reaction,
                keep_reagents=True,
                reagents_max_size=self.reagent_max_size,
            )
            return reaction
        except GeneralException:
            return None


class RebalanceReactionStandardizer:
    """Rebalance reaction."""

    def __init__(self, reagent_max_size: int = 7):
        self.reagent_max_size = reagent_max_size

    def __call__(self, reaction: ReactionContainer) -> ReactionContainer | None:
        """Rebalance reaction.

        :param reaction: Input reaction.
        :return: Returns rebalanced reaction, else None.
        """
        try:
            reaction = rebalance_reaction(reaction)
            return reaction
        except GeneralException:
            return None


def standardize_reaction(
    reaction: ReactionContainer, standardizers: list
) -> Tuple[bool, ReactionContainer] | None:
    """Remove duplicate reactions.

    :param reaction: Input reaction.
    :param standardizers: The list of standardizers.
    :return: Returns the standardized reaction, else None.
    """

    standardized_reaction = None
    with HiddenPrints():
        for standardizer in standardizers:
            standardized_reaction = standardizer(reaction)
            if not standardized_reaction:
                return None

    return standardized_reaction


@ray.remote
def process_batch(
    batch: List[ReactionContainer],
    standardizers: list,
) -> List[ReactionContainer]:
    """Processes a batch of reactions to standardize reactions based on the given list
    of standardizers.

    :param batch: A list of reactions to be standardized.
    :param standardizers: The list of standardizers.
    :return: The list of standardized reactions.
    """

    standardized_reaction_list = []
    for reaction in batch:
        standardized_reaction = standardize_reaction(reaction, standardizers)
        if standardized_reaction:
            standardized_reaction_list.append(standardized_reaction)
        else:
            continue
    return standardized_reaction_list


def process_completed_batch(
    futures: Dict,
    result_file: TextIOWrapper,
    n_processed: int,
) -> int:
    """Processes completed batches of standardized reactions.

    :param futures: A dictionary of futures with ongoing batch processing tasks.
    :param result_file: The path to the file where standardized reactions will be
        stored.
    :param n_processed: The number of already standardized reactions.
    :return: The number of standardized reactions after the processing of the current
        batch.
    """
    ready_id, running_id = ray.wait(list(futures.keys()), num_returns=1)
    completed_batch = ray.get(ready_id[0])

    # write results of the completed batch to file
    for reaction in completed_batch:
        result_file.write(reaction)
        n_processed += 1

    # remove completed future and update progress bar
    del futures[ready_id[0]]

    return n_processed


def standardize_reactions_from_file(
    input_reaction_data_path: str,
    standardized_reaction_data_path: str = "reaction_data_standardized.smi",
    num_cpus: int = 1,
    batch_size: int = 100,
) -> None:
    """Reactions standardization.

    :param input_reaction_data_path: Path to the reaction data file.
    :param standardized_reaction_data_path: Name for the file where standardized
        reactions will be stored.
    :param num_cpus: Number of CPUs to use for processing.
    :param batch_size: Size of the batch for processing reactions.
    :return: None. The function writes the processed reactions to specified smi/RDF
        files.
    """

    standardizers = [
        FunctionalGroupsStandardizer(),
        KekuleFormStandardizer(),
        CheckValenceStandardizer(),
        ImplicifyHydrogensStandardizer(),
        CheckIsotopesStandardizer(),
        SplitIonsStandardizer(),
        AromaticFormStandardizer(),
        MappingFixStandardizer(),
        UnchangedPartsStandardizer(),
        DuplicateReactionStandardizer(),
    ]

    ray.init(num_cpus=num_cpus, ignore_reinit_error=True, logging_level=logging.ERROR)
    max_concurrent_batches = num_cpus  # limit the number of concurrent batches

    with ReactionReader(input_reaction_data_path) as reactions, ReactionWriter(
        standardized_reaction_data_path
    ) as result_file:

        batches_to_process, batch = {}, []
        n_processed = 0
        for index, reaction in tqdm(
            enumerate(reactions),
            desc="Number of reactions processed: ",
            bar_format="{desc}{n} [{elapsed}]",
        ):

            batch.append(reaction)
            if len(batch) == batch_size:
                completed_batch = process_batch.remote(batch, standardizers)
                batches_to_process[completed_batch] = None
                batch = []

                # check and process completed tasks if reached the concurrency limit
                while len(batches_to_process) >= max_concurrent_batches:
                    n_processed = process_completed_batch(
                        batches_to_process, result_file, n_processed
                    )

        # process the last batch if it's not empty
        if batch:
            completed_batch = process_batch.remote(batch, standardizers)
            batches_to_process[completed_batch] = None

        # process remaining batches
        while batches_to_process:
            n_processed = process_completed_batch(
                batches_to_process, result_file, n_processed
            )

    ray.shutdown()

    print(f"Initial number of parsed reactions: {index + 1}")
    print(f"Standardized number of reactions: {n_processed}")
