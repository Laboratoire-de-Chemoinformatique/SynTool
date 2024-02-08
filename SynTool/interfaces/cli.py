"""
Module containing commands line scripts for training and planning mode
"""

import os
import shutil
import yaml
import warnings
from pathlib import Path

import click
import gdown

from SynTool.chem.data.cleaning import reactions_cleaner
from SynTool.chem.data.filtering import filter_reactions, ReactionCheckConfig
from SynTool.utils.loading import standardize_building_blocks
from SynTool.chem.reaction_rules.extraction import extract_rules_from_reactions
from SynTool.mcts.search import tree_search
from SynTool.ml.training.reinforcement import run_reinforcement_tuning
from SynTool.ml.training.supervised import create_policy_dataset, run_policy_training
from SynTool.utils.config import ReinforcementConfig, TreeConfig, PolicyNetworkConfig, ValueNetworkConfig
from SynTool.utils.config import ReactionStandardizationConfig, RuleExtractionConfig
from SynTool.chem.data.mapping import remove_reagents_and_map_from_file

warnings.filterwarnings("ignore")


@click.group(name="syntool")
def syntool():
    pass


@syntool.command(name="download_planning_data")
@click.option(
    "--root_dir",
    required=True,
    type=click.Path(exists=True),
    help="Path to the reaction database file that will be mapped.",
)
def download_planning_data_cli(root_dir='.'):
    """
    Downloads data for retrosythesis planning
    """
    remote_id = "1ygq9BvQgH2Tq_rL72BvSOdASSSbPFTsL"
    output = os.path.join(root_dir, "syntool_planning_data.zip")
    #
    gdown.download(output=output, id=remote_id, quiet=False)
    shutil.unpack_archive(output, root_dir)
    #
    os.remove(output)


@syntool.command(name='download_training_data')
@click.option(
    "--root_dir",
    required=True,
    type=click.Path(exists=True),
    help="Path to the reaction database file that will be mapped.",
)
def download_training_data_cli(root_dir='.'):
    """
    Downloads data for retrosythetic models training
    """
    remote_id = "1ckhO1l6xud0_bnC0rCDMkIlKRUMG_xs8"
    output = os.path.join(root_dir, "syntool_training_data.zip")
    #
    gdown.download(output=output, id=remote_id, quiet=False)
    shutil.unpack_archive(output, root_dir)
    #
    os.remove(output)


@syntool.command(name="building_blocks")
@click.option(
    "--input",
    "input_file",
    required=True,
    type=click.Path(exists=True),
    help="Path to the reaction database file that will be mapped.",
)
@click.option(
    "--output",
    "output_file",
    required=True,
    type=click.Path(),
    help="File where the results will be stored.",
)
def building_blocks_cli(input_file, output_file):
    """
    Standardizes building blocks
    """

    standardize_building_blocks(input_file=input_file, output_file=output_file)


@syntool.command(name="reaction_mapping")
@click.option(
    "--config",
    "config_path",
    required=True,
    type=click.Path(exists=True),
    help="Path to the configuration file. This file contains settings for mapping and standardizing reactions.",
)
@click.option(
    "--input",
    "input_file",
    required=True,
    type=click.Path(exists=True),
    help="Path to the reaction database file that will be mapped.",
)
@click.option(
    "--output",
    "output_file",
    default=Path("reaction_data_standardized.smi"),
    type=click.Path(),
    help="File where the results will be stored.",
)
def reaction_mapping_cli(config_path, input_file, output_file):
    """
    Reaction data mapping
    """

    stand_config = ReactionStandardizationConfig.from_yaml(config_path)
    remove_reagents_and_map_from_file(input_file=input_file, output_file=output_file, keep_reagent=stand_config.keep_reagents)


@syntool.command(name="reaction_standardizing")
@click.option(
    "--config",
    "config_path",
    required=True,
    type=click.Path(exists=True),
    help="Path to the configuration file. This file contains settings for mapping and standardizing reactions.",
)
@click.option(
    "--input",
    "input_file",
    required=True,
    type=click.Path(exists=True),
    help="Path to the reaction database file that will be mapped.",
)
@click.option(
    "--output",
    "output_file",
    type=click.Path(),
    help="File where the results will be stored.",
)
@click.option(
    "--num_cpus",
    default=8,
    type=int,
    help="Number of CPUs to use for processing. Defaults to 1.",
)
def reaction_standardizing_cli(config_path, input_file, output_file, num_cpus):
    """
    Standardizes reactions and remove duplicates
    """

    stand_config = ReactionStandardizationConfig.from_yaml(config_path)
    reactions_cleaner(config=stand_config,
                      input_file=input_file,
                      output_file=output_file,
                      num_cpus=num_cpus)


@syntool.command(name="reaction_filtering")
@click.option(
    "--config",
    "config_path",
    required=True,
    type=click.Path(exists=True),
    help="Path to the configuration file. This file contains settings for filtering reactions.",
)
@click.option(
    "--input",
    "input_file",
    required=True,
    type=click.Path(exists=True),
    help="Path to the reaction database file that will be mapped.",
)
@click.option(
    "--output",
    "output_file",
    default=Path("./"),
    type=click.Path(),
    help="File where the results will be stored.",
)
@click.option(
    "--append_results",
    is_flag=True,
    default=False,
    help="If set, results will be appended to existing files. By default, new files are created.",
)
@click.option(
    "--batch_size",
    default=100,
    type=int,
    help="Size of the batch for processing reactions. Defaults to 10.",
)
@click.option(
    "--num_cpus",
    default=8,
    type=int,
    help="Number of CPUs to use for processing. Defaults to 1.",
)
def reaction_filtering_cli(config_path,
                           input_file,
                           output_file,
                           append_results,
                           batch_size,
                           num_cpus):
    """
    Filters erroneous reactions
    """
    reaction_check_config = ReactionCheckConfig().from_yaml(config_path)
    filter_reactions(
        config=reaction_check_config,
        reaction_database_path=input_file,
        result_reactions_file_name=output_file,
        append_results=append_results,
        num_cpus=num_cpus,
        batch_size=batch_size,
    )


@syntool.command(name="rule_extracting")
@click.option(
    "--config",
    "config_path",
    required=True,
    type=click.Path(exists=True),
    help="Path to the configuration file. This file contains settings for reaction rules extraction.",
)
@click.option(
    "--input",
    "input_file",
    required=True,
    type=click.Path(exists=True),
    help="Path to the reaction database file that will be mapped.",
)
@click.option(
    "--output",
    "output_file",
    required=True,
    type=click.Path(),
    help="File where the results will be stored.",
)
@click.option(
    "--batch_size",
    default=100,
    type=int,
    help="Size of the batch for processing reactions. Defaults to 10.",
)
@click.option(
    "--num_cpus",
    default=8,
    type=int,
    help="Number of CPUs to use for processing. Defaults to 1.",
)
def rule_extracting_cli(
    config_path,
    input_file,
    output_file,
    num_cpus,
    batch_size,
):
    """
    Extracts reaction rules
    """

    reaction_rule_config = RuleExtractionConfig.from_yaml(config_path)
    extract_rules_from_reactions(config=reaction_rule_config,
                                 reaction_file=input_file,
                                 rules_file_name=output_file,
                                 num_cpus=num_cpus,
                                 batch_size=batch_size)


@syntool.command(name="supervised_ranking_policy_training")
@click.option(
    "--config",
    "config_path",
    required=True,
    type=click.Path(exists=True),
    help="Path to the configuration file. This file contains settings for policy training.",
)
@click.option(
    "--reaction_data",
    required=True,
    type=click.Path(exists=True),
    help="Path to the reaction database file that will be mapped.",
)
@click.option(
    "--reaction_rules",
    required=True,
    type=click.Path(exists=True),
    help="Path to the reaction database file that will be mapped.",
)
@click.option(
    "--results_dir",
    default=Path("."),
    type=click.Path(),
    help="Root directory where the results will be stored.",
)
@click.option(
    "--num_cpus",
    default=8,
    type=int,
    help="Number of CPUs to use for processing. Defaults to 1.",
)
def supervised_ranking_policy_training_cli(config_path, reaction_data, reaction_rules, results_dir, num_cpus):
    """
    Trains ranking policy network
    """

    policy_config = PolicyNetworkConfig.from_yaml(config_path)

    policy_dataset_file = os.path.join(results_dir, 'policy_dataset.ckpt')

    datamodule = create_policy_dataset(reaction_rules_path=reaction_rules,
                                       molecules_or_reactions_path=reaction_data,
                                       output_path=policy_dataset_file,
                                       dataset_type='ranking',
                                       batch_size=policy_config.batch_size,
                                       num_cpus=num_cpus)

    run_policy_training(datamodule, config=policy_config, results_path=results_dir)


@syntool.command(name="supervised_filtering_policy_training")
@click.option(
    "--config",
    "config_path",
    required=True,
    type=click.Path(exists=True),
    help="Path to the configuration file. This file contains settings for policy training.",
)
@click.option(
    "--molecules_file",
    required=True,
    type=click.Path(exists=True),
    help="Path to the molecules database file that will be mapped.",
)
@click.option(
    "--reaction_rules",
    required=True,
    type=click.Path(exists=True),
    help="Path to the reaction database file that will be mapped.",
)
@click.option(
    "--results_dir",
    default=Path("."),
    type=click.Path(),
    help="Root directory where the results will be stored.",
)
@click.option(
    "--num_cpus",
    default=8,
    type=int,
    help="Number of CPUs to use for processing. Defaults to 1.",
)
def supervised_filtering_policy_training_cli(config_path, molecules_file, reaction_rules, results_dir, num_cpus):
    """
    Trains filtering policy network
    """

    policy_config = PolicyNetworkConfig.from_yaml(config_path)

    policy_dataset_file = os.path.join(results_dir, 'policy_dataset.ckpt')
    datamodule = create_policy_dataset(reaction_rules_path=reaction_rules,
                                       molecules_or_reactions_path=molecules_file,
                                       output_path=policy_dataset_file,
                                       dataset_type='filtering',
                                       batch_size=policy_config.batch_size,
                                       num_cpus=num_cpus)

    run_policy_training(datamodule, config=policy_config, results_path=results_dir)


@syntool.command(name="reinforcement_value_network_training")
@click.option(
    "--config",
    required=True,
    type=click.Path(exists=True),
    help="Path to the configuration file. This file contains settings for policy training.",
)
@click.option(
    "--targets",
    required=True,
    type=click.Path(exists=True),
    help="Path to the configuration file. This file contains settings for policy training.",
)
@click.option(
    "--reaction_rules",
    required=True,
    type=click.Path(exists=True),
    help="Path to the configuration file. This file contains settings for policy training.",
)
@click.option(
    "--building_blocks",
    required=True,
    type=click.Path(exists=True),
    help="Path to the configuration file. This file contains settings for policy training.",
)
@click.option(
    "--policy_network",
    required=True,
    type=click.Path(exists=True),
    help="Path to the configuration file. This file contains settings for policy training.",
)
@click.option(
    "--value_network",
    default=None,
    type=click.Path(exists=True),
    help="Path to the configuration file. This file contains settings for policy training.",
)
@click.option(
    "--results_dir",
    default='.',
    type=click.Path(exists=False),
    help="Path to the configuration file. This file contains settings for policy training.",
)
def reinforcement_value_network_training_cli(config,
                                             targets,
                                             reaction_rules,
                                             building_blocks,
                                             policy_network,
                                             value_network,
                                             results_dir):
    """
    Trains value network with reinforcement learning
    """

    with open(config, "r") as file:
        config = yaml.safe_load(file)

    policy_config = PolicyNetworkConfig.from_dict(config['node_expansion'])
    policy_config.weights_path = policy_network

    value_config = ValueNetworkConfig.from_dict(config['value_network'])
    if value_network is None:
        value_config.weights_path = os.path.join(results_dir, 'weights', 'value_network.ckpt')

    tree_config = TreeConfig.from_dict(config['tree'])
    reinforce_config = ReinforcementConfig.from_dict(config['reinforcement'])

    run_reinforcement_tuning(targets_path=targets,
                             tree_config=tree_config,
                             policy_config=policy_config,
                             value_config=value_config,
                             reinforce_config=reinforce_config,
                             reaction_rules_path=reaction_rules,
                             building_blocks_path=building_blocks,
                             results_root=results_dir)


@syntool.command(name="planning")
@click.option(
    "--config",
    "config_path",
    required=True,
    type=click.Path(exists=True),
    help="Path to the configuration file. This file contains settings for policy training.",
)
@click.option(
    "--targets",
    required=True,
    type=click.Path(exists=True),
    help="Path to the configuration file. This file contains settings for policy training.",
)
@click.option(
    "--reaction_rules",
    required=True,
    type=click.Path(exists=True),
    help="Path to the configuration file. This file contains settings for policy training.",
)
@click.option(
    "--building_blocks",
    required=True,
    type=click.Path(exists=True),
    help="Path to the configuration file. This file contains settings for policy training.",
)
@click.option(
    "--policy_network",
    required=True,
    type=click.Path(exists=True),
    help="Path to the configuration file. This file contains settings for policy training.",
)
@click.option(
    "--value_network",
    default=None,
    type=click.Path(exists=True),
    help="Path to the configuration file. This file contains settings for policy training.",
)
@click.option(
    "--results_dir",
    default='.',
    type=click.Path(exists=False),
    help="Path to the configuration file. This file contains settings for policy training.",
)
def planning_cli(config_path,
                 targets,
                 reaction_rules,
                 building_blocks,
                 policy_network,
                 value_network,
                 results_dir):
    """
    Runs retrosynthesis planning
    """

    with open(config_path, "r") as file:
        config = yaml.safe_load(file)

    tree_config = TreeConfig.from_dict({**config['tree'], **config['node_evaluation']})
    policy_config = PolicyNetworkConfig.from_dict({**config['node_expansion'], **{'weights_path': policy_network}})

    tree_search(targets=targets,
                tree_config=tree_config,
                policy_config=policy_config,
                reaction_rules_path=reaction_rules,
                building_blocks_path=building_blocks,
                value_weights_path=value_network,
                results_root=results_dir)


if __name__ == '__main__':
    syntool()


