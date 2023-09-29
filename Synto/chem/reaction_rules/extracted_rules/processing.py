import logging
import os
from collections import defaultdict
from multiprocessing import Pool
from pickle import dump
from typing import Tuple

from CGRtools import RDFRead, RDFWrite, ReactionContainer
from .transformations import ReverseReaction
from tqdm import tqdm


def apply_transformations(transformations: list, reaction: ReactionContainer) -> ReactionContainer:
    """
    Applies transformations to given reaction

    :param transformations: list of transformations
    :param reaction: the reaction to be transformed
    :return: result reaction
    """
    for transform in transformations:
        if isinstance(reaction, list):  # like rules list obtained from 1 reaction
            reaction = [transform(real_reaction) for real_reaction in reaction]
        else:
            reaction = transform(reaction)
    return reaction


def apply_filters(reaction: ReactionContainer, reaction_filters) -> Tuple[bool, ReactionContainer]:
    """
    Applies filters to given reaction, return a reaction and bool

    :param reaction: input reaction
    :param reaction_filters: list of filters
    :return: reaction with marks in meta and True if there are at least one filter returned True
    """
    is_filtered = False
    for reaction_filter in reaction_filters:
        if reaction_filter(reaction):
            reaction.meta[reaction_filter.__class__.__name__] = 'True'
            is_filtered = True
    return is_filtered, reaction


def reaction_database_processing(reaction_database_file_name: str, transformations: list = None, filters: list = None,
                                 save_only_unique: bool = False, result_directory_name: str = './',
                                 filtered_reactions_file_name: str = 'filtered_reactions.rdf',
                                 result_reactions_file_name: str = 'reaction_rules.rdf',
                                 result_reactions_pkl_file_name: str = 'reaction_rules.pickle',
                                 remove_old_results: bool = False):
    """
    Applies given transformations and filters to reactions from the reaction database. Returns result reactions files in
    RDF and pickle (if save_only_unique is True) formats and filtered reactions file in RDF format

    :param reaction_database_file_name: path to the reaction database (.rdf format)
    :param transformations: list of transformations
    :param filters: list of filters
    :param save_only_unique: if True, then only unique reactions with information about frequency are saved
    :param result_directory_name: result directory name
    :param filtered_reactions_file_name: filtered and error reactions file name (.rdf)
    :param result_reactions_file_name: result reactions file name (.rdf)
    :param result_reactions_pkl_file_name: result reactions file name (.pickle)
    """
    os.makedirs(result_directory_name, exist_ok=True)

    if os.path.isfile(f'{result_directory_name}/{filtered_reactions_file_name}'):
        os.remove(f'{result_directory_name}/{filtered_reactions_file_name}')
        logging.warning(f"Removed {result_directory_name}/{filtered_reactions_file_name}")

    if os.path.isfile(f'{result_directory_name}/{result_reactions_file_name}'):
        os.remove(f'{result_directory_name}/{result_reactions_file_name}')
        logging.warning(f"Removed {result_directory_name}/{result_reactions_file_name}")

    if os.path.isfile(f'{result_directory_name}/unique_{result_reactions_file_name}'):
        os.remove(f'{result_directory_name}/unique_{result_reactions_file_name}')
        logging.warning(f"Removed {result_directory_name}/unique_{result_reactions_file_name}")

    # filtered_file_exist = os.path.isfile(f'{result_directory_name}/{filtered_reactions_file_name}')
    # results_file_exist = os.path.isfile(f'{result_directory_name}/{filtered_reactions_file_name}')
    # unique_file_exist = os.path.isfile(f'{result_directory_name}/unique_{result_reactions_file_name}')

    if save_only_unique:
        unique_reactions = defaultdict(list)

    with RDFRead(reaction_database_file_name, indexable=True) as reactions, \
            RDFWrite(f'{result_directory_name}/{filtered_reactions_file_name}', append=True) as filtered_file, \
            RDFWrite(f'{result_directory_name}/{result_reactions_file_name}', append=True) as result_file:
        reactions.reset_index()
        for n, reaction in tqdm(enumerate(reactions), total=len(reactions)):
            try:
                if filters:
                    is_filtered, reaction = apply_filters(reaction, filters)
                    if is_filtered:
                        filtered_file.write(reaction)
                        continue
                if transformations:  # TODO below reaction overwrite reaction is not good > reaction and reaction rules
                    reaction = apply_transformations(transformations, reaction)  # TODO probably rule extraction is not transformation
            except Exception:
                reaction.meta['Error'] = 'True'
                filtered_file.write(reaction)
            else:
                if type(reaction) != list:  # TODO isinstance ?
                    reaction = [reaction]
                for real_reaction in reaction:
                    real_reaction.clean2d()
                    if save_only_unique:
                        unique_reactions[real_reaction].append(n)
                    else:
                        real_reaction.meta['reaction_index'] = n
                    result_file.write(real_reaction)

    if save_only_unique:
        with RDFWrite(f'{result_directory_name}/unique_{result_reactions_file_name}') as unique_file:
            for result_reaction, reaction_ids in tqdm(unique_reactions.items()):
                result_reaction.meta['reaction_ids'] = ','.join([str(indx) for indx in reaction_ids])
                unique_file.write(result_reaction)
        with open(f'{result_directory_name}/{result_reactions_pkl_file_name}', 'wb') as pickle_file:

            unique_reactions = list(unique_reactions.keys())
            
            # reverse reaction rules
            reverse_reaction = ReverseReaction()
            unique_reactions = [reverse_reaction(i) for i in unique_reactions]

            dump(unique_reactions, pickle_file)


def reaction_database_multiprocessing(reaction_database_file_name: str, number_of_processes: int,
                                      transformations: list = None, filters: list = None,
                                      save_only_unique: bool = False, result_directory_name: str = './',
                                      filtered_reactions_file_name: str = 'filtered_reactions.rdf',
                                      result_reactions_file_name: str = 'result_reactions.rdf',
                                      result_reactions_pkl_file_name: str = 'result_reactions.pickle'):
    """
    Applies given transformations and filters to reactions from the reaction database (multiprocessing variant). Returns
    result reactions files in RDF and pickle (if save_only_unique is True) formats and filtered reactions file in RDF
    format

    :param reaction_database_file_name: path to the reaction database (.rdf format)
    :param number_of_processes: number of processes
    :param transformations: list of transformations
    :param filters: list of filters
    :param save_only_unique: if True, then only unique reactions with information about frequency are saved
    :param result_directory_name: result directory name
    :param filtered_reactions_file_name: filtered and error reactions file name (.rdf)
    :param result_reactions_file_name: result reactions file name (.rdf)
    :param result_reactions_pkl_file_name: result reactions file name (.pickle)
    """
    os.makedirs(result_directory_name, exist_ok=True)

    if os.path.isfile(f'{result_directory_name}/{filtered_reactions_file_name}'):
        os.remove(f'{result_directory_name}/{filtered_reactions_file_name}')

    if os.path.isfile(f'{result_directory_name}/{result_reactions_file_name}'):
        os.remove(f'{result_directory_name}/{result_reactions_file_name}')

    global _process_reaction

    def _process_reaction(reaction: ReactionContainer) -> Tuple[bool, ReactionContainer]:
        is_filtered = False
        try:
            if filters:
                is_filtered, reaction = apply_filters(reaction, filters)
            if transformations:
                reaction = apply_transformations(transformations, reaction)
        except Exception:
            reaction.meta['Error'] = 'True'
            is_filtered = True
        return is_filtered, reaction

    with RDFRead(reaction_database_file_name, indexable=True) as reactions:
        reactions.reset_index()

        with Pool(processes=number_of_processes) as pool:
            for is_filtered, result_reaction in tqdm(pool.imap_unordered(_process_reaction, reactions, chunksize=3),
                                                     total=len(reactions)):
                if is_filtered:
                    with RDFWrite(f'{result_directory_name}/{filtered_reactions_file_name}', append=True) as \
                            filtered_file:
                        filtered_file.write(result_reaction)
                else:
                    with RDFWrite(f'{result_directory_name}/{result_reactions_file_name}', append=True) as result_file:
                        if isinstance(result_reaction, list):
                            for real_reaction in result_reaction:
                                real_reaction.clean2d()
                                result_file.write(real_reaction)
                        else:
                            result_reaction.clean2d()
                            result_file.write(result_reaction)

    if save_only_unique and os.path.isfile(f'{result_directory_name}/{result_reactions_file_name}'):
        unique_reactions = defaultdict(int)

        with RDFRead(f'{result_directory_name}/{result_reactions_file_name}', indexable=True) as reactions:
            for reaction in reactions:
                unique_reactions[reaction] += 1

        with RDFWrite(f'{result_directory_name}/{result_reactions_file_name}') as result_file:
            with open(f'{result_directory_name}/{result_reactions_pkl_file_name}', 'wb') as result_file2:
                for result_reaction, number_of_reactions in unique_reactions.items():
                    result_reaction.meta['Number_of_reactions'] = number_of_reactions
                    result_file.write(result_reaction)
                    dump(result_reaction, result_file2)
