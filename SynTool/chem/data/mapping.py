"""Module containing functions for reactions mapping."""

from CGRtools import smiles as smiles_cgrtools
from chython import ReactionContainer
from chython import smiles as smiles_chython
from tqdm import tqdm

from SynTool.utils.files import ReactionReader, ReactionWriter
from SynTool.utils.logging import GeneralException


def map_and_remove_reagents(reaction: ReactionContainer) -> ReactionContainer:
    """Maps atoms of the reaction using chytorch.

    :param reaction: Reaction to be mapped.
    :return: Mapped reaction or None.
    """

    try:
        reaction.reset_mapping()
        reaction.remove_reagents()
    except GeneralException:
        return None

    return reaction


def map_and_remove_reagents_from_file(input_file: str, output_file: str) -> None:
    """Reads a file of reactions and maps atoms of the reactions using chytorch. This
    function does not use the ReactionReader/ReactionWriter classes, because they are
    not compatible with chython.

    :param input_file: The path and name of the input file.
    :param output_file: The path and name of the output file.
    :return: None.
    """

    if input_file == output_file:
        raise ValueError("input_file name and output_file name cannot be the same.")

    n_mapped = 0
    with ReactionReader(input_file) as inp_file, ReactionWriter(
        output_file
    ) as out_file:
        for cgrtools_reaction in tqdm(
            inp_file,
            desc="Number of reactions processed: ",
            bar_format="{desc}{n} [{elapsed}]",
        ):
            try:
                chython_reaction = smiles_chython(str(cgrtools_reaction))
                reaction_mapped = map_and_remove_reagents(chython_reaction)
                if reaction_mapped:
                    reaction_mapped_cgrtools = smiles_cgrtools(
                        format(chython_reaction, "m")
                    )
                    out_file.write(reaction_mapped_cgrtools)
                n_mapped += 1
            except:
                continue

    print(f"Number of mapped reactions: {n_mapped}")
