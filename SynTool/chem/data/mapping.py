"""
Module containing functions for reactions mapping.
"""

from tqdm import tqdm
from os.path import splitext
from pathlib import Path
from chython import smiles, RDFRead, RDFWrite, ReactionContainer
from chython.exceptions import IncorrectSmiles


def remove_reagents_and_map(reaction: ReactionContainer, keep_reagent: bool = False) -> ReactionContainer:
    """
    Maps atoms of the reaction using chytorch.

    :param reaction: Reaction to be mapped.
    :param keep_reagent: Whenever to remove reagent or not.

    :return: Mapped reaction or None.
    """

    try:
        reaction.reset_mapping()
    except:
        reaction.reset_mapping()  # successive reset_mapping works
    if not keep_reagent:
        try:
            reaction.remove_reagents()
        except:
            return None
    return reaction


def remove_reagents_and_map_from_file(input_file: str, output_file: str, keep_reagent: bool = False) -> None:
    """
    Reads a file of reactions and maps atoms of the reactions using chytorch.

    :param input_file: The path and name of the input file.
    :param output_file: The path and name of the output file.
    :param keep_reagent: Whenever to remove reagent or not.

    :return: None.
    """
    input_file = str(Path(input_file).resolve(strict=True))
    _, input_ext = splitext(input_file)
    if input_ext == ".smi":
        input_file = open(input_file, "r")
    elif input_ext == ".rdf":
        input_file = RDFRead(input_file, indexable=True)
    else:
        raise ValueError("File extension not recognized. File:", input_file, "- Please use smi or rdf file")
    enumerator = input_file if input_ext == ".rdf" else input_file.readlines()

    _, out_ext = splitext(output_file)
    if out_ext == ".smi":
        output_file = open(output_file, "w")
    elif out_ext == ".rdf":
        output_file = RDFWrite(output_file)
    else:
        raise ValueError("File extension not recognized. File:", output_file, "- Please use smi or rdf file")

    mapping_errors = 0
    parsing_errors = 0
    for reaction_smi in tqdm(enumerator, desc="Number of reactions processed: ", bar_format='{desc}{n} [{elapsed}]'):
        try:
            reaction = smiles(reaction_smi.strip('\n')) if input_ext == ".smi" else reaction_smi
        except IncorrectSmiles:
            parsing_errors += 1
            continue
        try:
            reaction_mapped = remove_reagents_and_map(reaction, keep_reagent)
        except:
            try:
                reaction_mapped = remove_reagents_and_map(smiles(str(reaction)), keep_reagent)
            except:
                mapping_errors += 1
                continue
        if reaction_mapped:
            reaction_smi_mapped = format(reaction, "m") + "\n" if out_ext == ".smi" else reaction
            output_file.write(reaction_smi_mapped)
        else:
            mapping_errors += 1

    input_file.close()
    output_file.close()

    if parsing_errors:
        print(parsing_errors, "reactions couldn't be parsed")
    if mapping_errors:
        print(mapping_errors, "reactions couldn't be mapped")
