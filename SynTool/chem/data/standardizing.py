"""
Module containing classes and functions for reactions standardizing.
"""

import os
from tqdm import tqdm
from logging import getLogger, RootLogger
from multiprocessing import Queue, Process, Manager
from CGRtools.containers import ReactionContainer
from SynTool.chem.data.standardizer import Standardizer
from SynTool.utils.files import ReactionReader, ReactionWriter
from SynTool.utils.config import ReactionStandardizationConfig



def cleaner(reaction: ReactionContainer, logger: RootLogger, config: ReactionStandardizationConfig) -> ReactionContainer:
    """
    Standardizes a reaction according to external script.

    :param reaction: Reaction to be standardized.
    :param logger: Logger - to avoid writing log.
    :param config: ReactionStandardizationConfig.

    :return: Standardized reaction or empty list.
    """
    standardizer = Standardizer(id_tag='Reaction_ID',
                                action_on_isotopes=2,
                                skip_tautomerize=True,
                                skip_errors=config.skip_errors,
                                keep_unbalanced_ions=config.keep_unbalanced_ions,
                                keep_reagents=config.keep_reagents,
                                ignore_mapping=config.ignore_mapping,
                                logger=logger)

    return standardizer.standardize(reaction)


def worker_cleaner(to_clean: Queue, to_write: Queue, config: ReactionStandardizationConfig) -> None:
    """
    Launches reaction standardization using the Queue to_clean. Fills the to_write Queue with results.

    :param to_clean: Queue of reactions to be standardized.
    :param to_write: Queue of standardized reactions to be written.
    :param config: ReactionStandardizationConfig.

    :return: None.
    """
    logger = getLogger()
    logger.disabled = True

    while True:
        raw_reaction = to_clean.get()
        if raw_reaction == "Quit":
            break
        res = cleaner(raw_reaction, logger, config)
        to_write.put(res)

    logger.disabled = False


def cleaner_writer(output_file: str, to_write: ReactionContainer, cleaned_nb: int, remove_old: bool = True) -> None:
    """
    Writes standardized reactions to the output file.

    :param output_file: The output file path.
    :param to_write: Standardized reaction to be writen.
    :param cleaned_nb: The number of reactions to be writen.
    :param remove_old: Whenever to remove or not an already existing file.

    :return: None.
    """

    if remove_old and os.path.isfile(output_file):
        os.remove(output_file)

    counter = 0
    seen_reactions = []
    with ReactionWriter(output_file) as out:
        while True:
            res = to_write.get()
            if res:
                if res == "Quit":
                    cleaned_nb.set(counter)
                    break
                elif isinstance(res, ReactionContainer):
                    smi = format(res, "m")
                    if smi not in seen_reactions:
                        out.write(res)
                        counter += 1
                        seen_reactions.append(smi)


def reactions_cleaner(config: ReactionStandardizationConfig, input_file: str, output_file: str, num_cpus: int,
                      batch_prep_size: int = 100) -> None:
    """
    Writes standardized reactions to the output file.

    :param config: ReactionStandardizationConfig.
    :param input_file: Input reaction data file path.
    :param output_file: Output reaction data file path.
    :param num_cpus: The number of CPU to be parallelized.
    :param batch_prep_size: The size of batch of reactions per CPU.

    :return: None.
    """
    with Manager() as m:
        to_clean = m.Queue(maxsize=num_cpus * batch_prep_size)
        to_write = m.Queue(maxsize=batch_prep_size)
        cleaned_nb = m.Value(int, 0)

        writer = Process(target=cleaner_writer, args=(output_file, to_write, cleaned_nb))
        writer.start()

        workers = []
        for _ in range(num_cpus - 2):
            w = Process(target=worker_cleaner, args=(to_clean, to_write, config))
            w.start()
            workers.append(w)

        n = 0
        with ReactionReader(input_file) as reactions:
            for raw_reaction in tqdm(reactions, desc="Number of reactions processed: ",
                                     bar_format='{desc}{n} [{elapsed}]'):

                if 'Reaction_ID' not in raw_reaction.meta:
                    raw_reaction.meta['Reaction_ID'] = n
                to_clean.put(raw_reaction)
                n += 1

        for _ in workers:
            to_clean.put("Quit")
        for w in workers:
            w.join()

        to_write.put("Quit")
        writer.join()

        print(f'Initial number of reactions: {n}'),
        print(f'Removed number of reactions: {n - cleaned_nb.get()}')
