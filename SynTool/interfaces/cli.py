"""
Module containing commands line scripts for training and planning mode
"""

import warnings
import os
import shutil
from pathlib import Path
import click
import gdown

from SynTool.chem.reaction_rules.extraction import extract_rules_from_reactions
from SynTool.chem.data.cleaning import reactions_cleaner
from SynTool.chem.data.mapping import remove_reagents_and_map_from_file
from SynTool.utils.loading import standardize_building_blocks
from SynTool.ml.training import create_policy_dataset, run_policy_training
from SynTool.ml.training.reinforcement import run_self_tuning
from SynTool.ml.networks.policy import PolicyNetworkConfig
from SynTool.utils.config import read_planning_config, read_training_config, TreeConfig
from SynTool.mcts.search import tree_search

from SynTool.chem.data.filtering import (
    filter_reactions,
    ReactionCheckConfig,
    CCRingBreakingConfig,
    WrongCHBreakingConfig,
    CCsp3BreakingConfig,
    DynamicBondsConfig,
    MultiCenterConfig,
    NoReactionConfig,
    SmallMoleculesConfig,
)

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


@main.command(name='syntool_planning')
@click.option("--config",
              "config_path",
              required=True,
              help="Path to the config YAML molecules_path.",
              type=click.Path(exists=True, path_type=Path),
              )
def syntool_planning_cli(config_path):
    """
    Launches tree search for the given target molecules and stores search statistics and found retrosynthetic paths

    :param config_path: The path to the configuration file that contains the settings and parameters for the tree search
    """
    config = read_planning_config(config_path)
    config['Tree']['silent'] = True

    # standardize building blocks
    if config['InputData']['standardize_building_blocks']:
        print('STANDARDIZE BUILDING BLOCKS ...')
        standardize_building_blocks(config['InputData']['building_blocks_path'],
                                    config['InputData']['building_blocks_path'])
    # run planning
    print('\nRUN PLANNING ...')
    tree_config = TreeConfig.from_dict(config['Tree'])
    tree_search(targets=config['General']['targets_path'],
                tree_config=tree_config,
                reaction_rules_path=config['InputData']['reaction_rules_path'],
                building_blocks_path=config['InputData']['building_blocks_path'],
                policy_weights_path=config['PolicyNetwork']['weights_path'],
                value_weights_paths=config['ValueNetwork']['weights_path'],
                results_root=config['General']['results_root'])


@main.command(name='syntool_training')
@click.option(
    "--config",
    "config_path",
    required=True,
    help="Path to the config YAML file.",
    type=click.Path(exists=True, path_type=Path)
             )
def syntool_training_cli(config_path):

    # read training config
    print('READ CONFIG ...')
    config = read_training_config(config_path)
    print('Config is read')

    reaction_data_file = config['InputData']['reaction_data_path']

    # reaction data mapping
    data_output_folder = os.path.join(config['General']['results_root'], 'reaction_data')
    Path(data_output_folder).mkdir(parents=True, exist_ok=True)
    mapped_data_file = os.path.join(data_output_folder, 'reaction_data_mapped.smi')
    if config['DataCleaning']['map_reactions']:
        print('\nMAP REACTION DATA ...')

        remove_reagents_and_map_from_file(input_file=config['InputData']['reaction_data_path'],
                                          output_file=mapped_data_file)

        reaction_data_file = mapped_data_file

    # reaction data cleaning
    cleaned_data_file = os.path.join(data_output_folder, 'reaction_data_cleaned.rdf')
    if config['DataCleaning']['clean_reactions']:
        print('\nCLEAN REACTION DATA ...')

        reactions_cleaner(input_file=reaction_data_file,
                          output_file=cleaned_data_file,
                          num_cpus=config['General']['num_cpus'])

        reaction_data_file = cleaned_data_file

    # reactions data filtering
    if config['DataCleaning']['filter_reactions']:
        print('\nFILTER REACTION DATA ...')
        #
        filtration_config = ReactionCheckConfig(
            remove_small_molecules=False,
            small_molecules_config=SmallMoleculesConfig(limit=6),
            dynamic_bonds_config=DynamicBondsConfig(min_bonds_number=1, max_bonds_number=6),
            no_reaction_config=NoReactionConfig(),
            multi_center_config=MultiCenterConfig(),
            wrong_ch_breaking_config=WrongCHBreakingConfig(),
            cc_sp3_breaking_config=CCsp3BreakingConfig(),
            cc_ring_breaking_config=CCRingBreakingConfig()
        )

        filtered_data_file = os.path.join(data_output_folder, 'reaction_data_filtered.rdf')
        filter_reactions(config=filtration_config,
                         reaction_database_path=reaction_data_file,
                         result_directory_path=data_output_folder,
                         result_reactions_file_name='reaction_data_filtered',
                         num_cpus=config['General']['num_cpus'],
                         batch_size=100)

        reaction_data_file = filtered_data_file

    # standardize building blocks
    if config['DataCleaning']['standardize_building_blocks']:
        print('\nSTANDARDIZE BUILDING BLOCKS ...')

        standardize_building_blocks(config['InputData']['building_blocks_path'],
                                    config['InputData']['building_blocks_path'])

    # reaction rules extraction
    print('\nEXTRACT REACTION RULES ...')

    rules_output_folder = os.path.join(config['General']['results_root'], 'reaction_rules')
    Path(rules_output_folder).mkdir(parents=True, exist_ok=True)
    reaction_rules_path = os.path.join(rules_output_folder, 'reaction_rules_filtered.pickle')
    config['InputData']['reaction_rules_path'] = reaction_rules_path

    extract_rules_from_reactions(config=config,
                                 reaction_file=reaction_data_file,
                                 results_root=rules_output_folder,
                                 num_cpus=config['General']['num_cpus'])

    # create policy network dataset
    print('\nCREATE POLICY NETWORK DATASET ...')
    policy_output_folder = os.path.join(config['General']['results_root'], 'policy_network')
    Path(policy_output_folder).mkdir(parents=True, exist_ok=True)
    policy_data_file = os.path.join(policy_output_folder, 'policy_dataset.pt')

    if config['PolicyNetwork']['policy_type'] == 'ranking':
        molecules_or_reactions_path = reaction_data_file
    elif config['PolicyNetwork']['policy_type'] == 'filtering':
        molecules_or_reactions_path = config['InputData']['policy_data_path']
    else:
        raise ValueError(
            "Invalid policy_type. Allowed values are 'ranking', 'filtering'."
        )

    datamodule = create_policy_dataset(reaction_rules_path=reaction_rules_path,
                                       molecules_or_reactions_path=molecules_or_reactions_path,
                                       output_path=policy_data_file,
                                       dataset_type=config['PolicyNetwork']['policy_type'],
                                       batch_size=config['PolicyNetwork']['batch_size'],
                                       num_cpus=config['General']['num_cpus'])

    # train policy network
    print('\nTRAIN POLICY NETWORK ...')
    policy_config = PolicyNetworkConfig.from_dict(config['PolicyNetwork'])
    run_policy_training(datamodule, config=policy_config, results_path=policy_output_folder)
    config['PolicyNetwork']['weights_path'] = os.path.join(policy_output_folder, 'weights', 'policy_network.ckpt')

    # self-tuning value network training
    print('\nTRAIN VALUE NETWORK ...')
    value_output_folder = os.path.join(config['General']['results_root'], 'value_network')
    Path(value_output_folder).mkdir(parents=True, exist_ok=True)
    config['ValueNetwork']['weights_path'] = os.path.join(value_output_folder, 'weights', 'value_network.ckpt')

    run_self_tuning(config, results_root=value_output_folder)


if __name__ == '__main__':
    main()
