"""
Module containing commands line scripts for training and planning steps.
"""

import os
import shutil
import yaml
import warnings
import click
import gdown
from pathlib import Path
from SynTool.chem.data.standardizing import reactions_cleaner
from SynTool.chem.data.filtering import filter_reactions, ReactionCheckConfig
from SynTool.chem.utils import canonicalize_building_blocks
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
def download_planning_data_cli() -> None:
    """
    Downloads data for retrosythesis planning (reaction/molecule data and trained neural networks).
    """
    remote_id = "1HFL8yT5i2wE82lNqB88wZ5OM2D9AsvXH"
    data_archive = os.path.join("syntool_planning_data.zip")
    #
    gdown.download(output=data_archive, id=remote_id, quiet=False)
    shutil.unpack_archive(data_archive)
    os.remove(data_archive)


@syntool.command(name='download_training_data')
def download_training_data_cli() -> None:
    """
    Downloads data for retrosythetic models training.
    """
    remote_id = "1I2u4Zn-et-tlHmdLBAqclGiAiUuA1X5G"
    data_archive = os.path.join("syntool_training_data.zip")
    #
    gdown.download(output=data_archive, id=remote_id, quiet=False)
    shutil.unpack_archive(data_archive)
    os.remove(data_archive)


@syntool.command(name="building_blocks")
@click.option( "--input", "input_file", required=True, type=click.Path(exists=True),
               help="Path to the file with building blocks to be standardized.")
@click.option("--output", "output_file", required=True, type=click.Path(),
              help="Path to the file where standardized building blocks will be stored.")
def building_blocks_cli(input_file: str, output_file: str) -> None:
    """
    Standardizes building blocks.
    """
    canonicalize_building_blocks(input_file=input_file, output_file=output_file)


@syntool.command(name="reaction_mapping")
@click.option("--input", "input_file", required=True, type=click.Path(exists=True),
              help="Path to the file with reactions to be mapped.")
@click.option("--output", "output_file", default=Path("reaction_data_standardized.smi"), type=click.Path(),
              help="Path to the file where mapped reactions will be stored.")
def reaction_mapping_cli(input_file: str, output_file: str) -> None:
    """
    Reaction data mapping.
    """
    remove_reagents_and_map_from_file(input_file=input_file, output_file=output_file, keep_reagent=False)


@syntool.command(name="reaction_standardizing")
@click.option("--config", "config_path", required=True, type=click.Path(exists=True),
              help="Path to the configuration file for reactions standardizing.")
@click.option("--input", "input_file", required=True, type=click.Path(exists=True),
              help="Path to the file with reactions to be standardized.")
@click.option("--output", "output_file", type=click.Path(),
              help="Path to the file where standardized reactions will be stored.")
@click.option("--num_cpus", default=4, type=int,
              help="The number of CPUs to use for processing.")
def reaction_standardizing_cli(config_path: str, input_file: str, output_file: str, num_cpus: int) -> None:
    """
    Standardizes reactions and remove duplicates.
    """
    stand_config = ReactionStandardizationConfig.from_yaml(config_path)
    reactions_cleaner(config=stand_config,
                      input_file=input_file,
                      output_file=output_file,
                      num_cpus=num_cpus)


@syntool.command(name="reaction_filtering")
@click.option("--config", "config_path", required=True, type=click.Path(exists=True),
              help="Path to the configuration file for reactions filtering.")
@click.option("--input", "input_file", required=True, type=click.Path(exists=True),
              help="Path to the file with reactions to be filtered.")
@click.option("--output", "output_file", default=Path("./"), type=click.Path(),
              help="Path to the file where successfully filtered reactions will be stored.")
@click.option("--num_cpus", default=4, type=int,
              help="The number of CPUs to use for processing.")
def reaction_filtering_cli(config_path: str, input_file: str, output_file: str, num_cpus: int):
    """
    Filters erroneous reactions.
    """
    reaction_check_config = ReactionCheckConfig().from_yaml(config_path)
    filter_reactions(config=reaction_check_config, input_reaction_data_path=input_file,
                     filtered_reaction_data_path=output_file, append_results=True,
                     num_cpus=num_cpus, batch_size=100)


@syntool.command(name="rule_extracting")
@click.option("--config", "config_path", required=True, type=click.Path(exists=True),
              help="Path to the configuration file for reaction rules extracting.")
@click.option("--input", "input_file", required=True, type=click.Path(exists=True),
              help="Path to the file with reactions for reaction rules extraction.")
@click.option("--output", "output_file", required=True, type=click.Path(),
              help="Path to the file where extracted reaction rules will be stored.")
@click.option("--num_cpus", default=4, type=int,
              help="The number of CPUs to use for processing.")
def rule_extracting_cli(config_path: str, input_file: str, output_file: str, num_cpus: int):
    """
    Reaction rules extraction.
    """
    reaction_rule_config = RuleExtractionConfig.from_yaml(config_path)
    extract_rules_from_reactions(config=reaction_rule_config, reaction_file=input_file, rules_file_name=output_file,
                                 num_cpus=num_cpus, batch_size=100)


@syntool.command(name="supervised_ranking_policy_training")
@click.option("--config", "config_path", required=True, type=click.Path(exists=True),
              help="Path to the configuration file for ranking policy training.")
@click.option("--reaction_data", required=True, type=click.Path(exists=True),
              help="Path to the file with reactions for ranking policy training.")
@click.option("--reaction_rules", required=True, type=click.Path(exists=True),
              help="Path to the file with extracted reaction rules.")
@click.option("--results_dir", default=Path("."), type=click.Path(),
              help="Path to the directory where the trained policy network will be stored.")
@click.option("--num_cpus", default=4, type=int,
              help="The number of CPUs to use for training set preparation.")
def supervised_ranking_policy_training_cli(config_path: str, reaction_data: str, reaction_rules: str,
                                           results_dir: str , num_cpus: int) -> None:
    """
    Ranking policy network training.
    """
    policy_config = PolicyNetworkConfig.from_yaml(config_path)
    policy_config.policy_type = 'ranking'
    policy_dataset_file = os.path.join(results_dir, 'policy_dataset.dt')

    datamodule = create_policy_dataset(reaction_rules_path=reaction_rules,
                                       molecules_or_reactions_path=reaction_data,
                                       output_path=policy_dataset_file,
                                       dataset_type='ranking',
                                       batch_size=policy_config.batch_size,
                                       num_cpus=num_cpus)

    run_policy_training(datamodule, config=policy_config, results_path=results_dir)


@syntool.command(name="supervised_filtering_policy_training")
@click.option("--config", "config_path", required=True, type=click.Path(exists=True),
              help="Path to the configuration file for filtering policy training.")
@click.option("--molecule_data", required=True, type=click.Path(exists=True),
              help="Path to the file with molecules for filtering policy training.")
@click.option( "--reaction_rules", required=True, type=click.Path(exists=True),
               help="Path to the file with extracted reaction rules.")
@click.option("--results_dir", default=Path("."), type=click.Path(),
              help="Path to the directory where the trained policy network will be stored.")
@click.option("--num_cpus", default=8, type=int,
              help="The number of CPUs to use for training set preparation.")
def supervised_filtering_policy_training_cli(config_path: str, molecule_data: str, reaction_rules: str,
                                             results_dir: str, num_cpus: int):
    """
    Filtering policy network training.
    """

    policy_config = PolicyNetworkConfig.from_yaml(config_path)
    policy_config.policy_type = 'filtering'
    policy_dataset_file = os.path.join(results_dir, 'policy_dataset.ckpt')

    datamodule = create_policy_dataset(reaction_rules_path=reaction_rules,
                                       molecules_or_reactions_path=molecule_data,
                                       output_path=policy_dataset_file,
                                       dataset_type='filtering',
                                       batch_size=policy_config.batch_size,
                                       num_cpus=num_cpus)

    run_policy_training(datamodule, config=policy_config, results_path=results_dir)


@syntool.command(name="reinforcement_value_network_training")
@click.option("--config", "config_path", required=True, type=click.Path(exists=True),
              help="Path to the configuration file for value network training.")
@click.option("--targets", required=True, type=click.Path(exists=True),
              help="Path to the file with target molecules for planning simulations.")
@click.option("--reaction_rules", required=True, type=click.Path(exists=True),
              help="Path to the file with extracted reaction rules. Needed for planning simulations.")
@click.option("--building_blocks", required=True, type=click.Path(exists=True),
              help="Path to the file with building blocks. Needed for planning simulations.")
@click.option("--policy_network", required=True, type=click.Path(exists=True),
              help="Path to the file with trained policy network. Needed for planning simulations.")
@click.option("--value_network", default=None, type=click.Path(exists=True),
              help="Path to the file with trained value network. Needed in case of additional value network fine-tuning")
@click.option("--results_dir", default='.', type=click.Path(exists=False),
              help="Path to the directory where the trained value network will be stored.")
def reinforcement_value_network_training_cli(config_path: str, targets: str, reaction_rules: str, building_blocks: str,
                                             policy_network: str, value_network: str, results_dir: str):
    """
    Value network reinforcement training.
    """

    with open(config_path, "r") as file:
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
@click.option("--config", "config_path", required=True, type=click.Path(exists=True),
              help="Path to the configuration file for retrosynthesis planning.")
@click.option("--targets", required=True, type=click.Path(exists=True),
              help="Path to the file with target molecules for retrosynthesis planning.")
@click.option("--reaction_rules", required=True, type=click.Path(exists=True),
              help="Path to the file with extracted reaction rules.")
@click.option("--building_blocks", required=True, type=click.Path(exists=True),
              help="Path to the file with building blocks.")
@click.option("--policy_network", required=True, type=click.Path(exists=True),
              help="Path to the file with trained policy network.")
@click.option("--value_network", default=None, type=click.Path(exists=True),
              help="Path to the file with trained value network.")
@click.option("--results_dir", default='.', type=click.Path(exists=False),
              help="Path to the file where retrosynthesis planning results will be stored.")
def planning_cli(config_path: str, targets: str, reaction_rules: str, building_blocks: str,
                 policy_network: str, value_network: str, results_dir: str):
    """
    Retrosynthesis planning.
    """

    with open(config_path, "r") as file:
        config = yaml.safe_load(file)

    search_config = {**config['tree'], **config['node_evaluation']}
    policy_config = PolicyNetworkConfig.from_dict({**config['node_expansion'], **{'weights_path': policy_network}})

    tree_search(targets_path=targets,
                search_config=search_config,
                policy_config=policy_config,
                reaction_rules_path=reaction_rules,
                building_blocks_path=building_blocks,
                value_network_path=value_network,
                results_root=results_dir)


if __name__ == '__main__':
    syntool()


