"""
Module containing commands line scripts for training and planning mode
"""

import warnings
import os
import shutil
from pathlib import Path
import click
import gdown

from Synto.chem.reaction_rules.extraction import extract_rules_from_reactions
from Synto.chem.data.cleaning import reactions_cleaner
from Synto.ml.training import create_policy_training_set, run_policy_training
from Synto.ml.training.reinforcement import run_self_tuning
from Synto.chem.loading import canonicalize_building_blocks
from Synto.utils.config import read_planning_config, read_training_config
from Synto.mcts.search import tree_search
from Synto.chem.loading import load_reaction_rules

warnings.filterwarnings("ignore")
main = click.Group()


@main.command(name='planning_data')
def planning_data_cli():
    """
    Downloads a file from Google Drive using its remote ID, saves it as a zip file, extracts the contents,
    and then deletes the zip file
    """
    remote_id = '1c5YJDT-rP1ZvFA-ELmPNTUj0b8an4yFf'
    output = 'synto_planning_data.zip'
    #
    gdown.download(output=output, id=remote_id, quiet=True)
    shutil.unpack_archive(output, './')
    #
    os.remove(output)


@main.command(name='training_data')
def training_data_cli():
    """
    Downloads a file from Google Drive using its remote ID, saves it as a zip file, extracts the contents,
    and then deletes the zip file
    """
    remote_id = '1r4I7OskGvzg-zxYNJ7WVYpVR2HSYW10N'
    output = 'synto_training_data.zip'
    #
    gdown.download(output=output, id=remote_id, quiet=True)
    shutil.unpack_archive(output, './')
    #
    os.remove(output)


@main.command(name='building_blocks')
@click.option(
    "--input",
    "input_file",
    required=True,
    help="Path to the file with original building blocks",
    type=click.Path(exists=True),
)
@click.option(
    "--output",
    "output_file",
    required=True,
    help="Path to the file with processed building blocks",
    type=click.Path(exists=True),
)
def building_blocks_cli(input_file, output_file):
    """
    Canonicalizes custom building blocks
    """
    canonicalize_building_blocks(input_file, output_file)


@main.command(name='synto_planning')
@click.option(
    "--targets",
    "targets_file",
    help="Path to targets SDF molecules_path. The name of molecules_path will be used to save report.",
    type=click.Path(exists=True),
)
@click.option("--config", "config_path",
              required=True,
              help="Path to the config YAML molecules_path. To generate default config, use command Synto_default_config",
              type=click.Path(exists=True, path_type=Path),
              )
@click.option(
    "--results_root",
    help="Path to the folder where to save all statistics and results",
    required=True,
    type=click.Path(path_type=Path),
)
def synto_planning_cli(targets_file, config_path, results_root):
    """
    Launches tree search for the given target molecules and stores search statistics and found retrosynthetic paths

    :param targets_file: The path to a file that contains the list of targets for tree search
    :param config_path: The path to the configuration file that contains the settings and parameters for the tree search
    :param results_root: The root directory where the search results will be saved
    """
    config = read_planning_config(config_path)
    config['Tree']['verbose'] = False
    tree_search(results_root, targets_file, config)


@main.command(name='synto_training')
@click.option(
    "--config",
    "config",
    required=True,
    help="Path to the config YAML file.",
    type=click.Path(exists=True, path_type=Path)
)
def synto_training_cli(config):

    # read training config
    print('READ CONFIG ...')
    config = read_training_config(config)
    print('Config is read')

    # reaction mapping
    pass

    # reaction data cleaning
    if config['DataCleaning']['clean_reactions']:
        print('\nCLEAN REACTION DATA ...')

        output_folder = os.path.join(config['General']['results_root'], 'reaction_data')
        Path(output_folder).mkdir(parents=True, exist_ok=True)
        cleaned_data_file = os.path.join(output_folder, 'reaction_data_cleaned.rdf')

        reactions_cleaner(input_file=config['InputData']['reaction_data_path'],
                          output_file=cleaned_data_file,
                          num_cpus=config['General']['num_cpus'])

    # reaction rules extraction
    print('\nEXTRACT REACTION RULES ...')
    if config['DataCleaning']['clean_reactions']:
        reaction_file = cleaned_data_file
    else:
        reaction_file = config['InputData']['reaction_data_path']

    reaction_rules_folder = os.path.join(config['General']['results_root'], 'reaction_rules')
    Path(reaction_rules_folder).mkdir(parents=True, exist_ok=True)

    extract_rules_from_reactions(reaction_file=reaction_file,
                                 results_root=reaction_rules_folder,
                                 min_popularity=config['ReactionRules']['min_popularity'],
                                 num_cpus=config['General']['num_cpus'])

    # create policy network dataset
    print('\nCREATE POLICY NETWORK DATASET ...')

    reaction_rules_path = os.path.join(reaction_rules_folder, 'reaction_rules_filtered.pickle')
    config['InputData']['reaction_rules_path'] = reaction_rules_path

    policy_output_folder = os.path.join(config['General']['results_root'], 'policy_network')
    Path(policy_output_folder).mkdir(parents=True, exist_ok=True)
    policy_data_file = os.path.join(policy_output_folder, 'policy_dataset.pt')

    datamodule = create_policy_training_set(reaction_rules_path=reaction_rules_path,
                                            molecules_path=config['InputData']['policy_data_path'],
                                            output_path=policy_data_file,
                                            batch_size=config['PolicyNetwork']['batch_size'],
                                            num_cpus=config['General']['num_cpus'])

    # train policy network
    print('\nTRAIN POLICY NETWORK ...')
    n_rules = len(load_reaction_rules(reaction_rules_path))
    run_policy_training(datamodule, config, n_rules=n_rules, results_path=policy_output_folder)
    config['PolicyNetwork']['weights_path'] = os.path.join(policy_output_folder, 'policy_network.ckpt')

    # self-tuning value network training
    print('\nTRAIN VALUE NETWORK ...')
    value_output_folder = os.path.join(config['General']['results_root'], 'value_network')
    Path(value_output_folder).mkdir(parents=True, exist_ok=True)

    config['ValueNetwork']['weights_path'] = os.path.join(value_output_folder, 'value_network.ckpt')
    run_self_tuning(config, results_root=value_output_folder)


if __name__ == '__main__':
    main()
