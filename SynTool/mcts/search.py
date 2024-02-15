"""
Module containing functions for running tree search for the set of target molecules
"""

import csv
import json
from pathlib import Path

from tqdm import tqdm

from SynTool.interfaces.visualisation import to_table, extract_routes
from SynTool.mcts.tree import Tree, TreeConfig
from SynTool.mcts.evaluation import ValueFunction
from SynTool.mcts.expansion import PolicyFunction
from SynTool.utils import path_type
from SynTool.utils.files import MoleculeReader
from SynTool.utils.config import PolicyNetworkConfig


def extract_tree_stats(tree, target):
    """
    Collects various statistics from a tree and returns them in a dictionary format

    :param tree: The retro tree.
    :param target: The target molecule or compound that you want to search for in the tree. It is
    expected to be a string representing the SMILES notation of the target molecule
    :return: A dictionary with the calculated statistics
    """
    newick_tree, newick_meta = tree.newickify(visits_threshold=0)
    newick_meta_line = ";".join([f"{nid},{v[0]},{v[1]},{v[2]}" for nid, v in newick_meta.items()])
    return {
        "target_smiles": str(target),
        "tree_size": len(tree),
        "search_time": round(tree.curr_time, 1),
        "found_paths": len(tree.winning_nodes),
        "newick_tree": newick_tree,
        "newick_meta": newick_meta_line,
    }


def tree_search(
        targets_path: path_type,
        tree_config: TreeConfig,
        policy_config: PolicyNetworkConfig,
        reaction_rules_path: path_type,
        building_blocks_path: path_type,
        policy_weights_path: path_type = None,  # TODO not used
        value_weights_path: path_type = None,
        results_root: path_type = "search_results"
):
    """
    Performs a tree search on a set of target molecules using specified configuration and rules,
    logging the results and statistics.

    :param tree_config: The config object containing the configuration for the tree search.
    :param policy_config: The config object containing the configuration for the policy.
    :param reaction_rules_path: The path to the file containing reaction rules.
    :param building_blocks_path: The path to the file containing building blocks.
    :param targets_path: The path to the file containing the target molecules (in SDF or SMILES format).
    :param value_weights_path: The path to the file containing value weights (optional).
    :param results_root: The path to the directory where the results of the tree search will be saved. Defaults to 'search_results/'.
    :param retropaths_files_name: The base name for the files that will be generated to store the retro paths. Defaults to 'retropath'. #TODO arg dont exist

    This function configures and executes a tree search algorithm, leveraging reaction rules and building blocks
    to find synthetic pathways for given target molecules. The results, including paths and statistics, are
    saved in the specified directory. Logging is used to record the process and any issues encountered.
    """

    targets_file = Path(targets_path)

    # results folder
    results_root = Path(results_root)
    if not results_root.exists():
        results_root.mkdir()

    # output files
    stats_file = results_root.joinpath("tree_search_stats.csv")
    paths_file = results_root.joinpath("extracted_paths.json")
    retropaths_folder = results_root.joinpath("retropaths")
    retropaths_folder.mkdir(exist_ok=True)

    # stats header
    stats_header = ["target_smiles", "tree_size", "search_time",
                    "found_paths", "newick_tree", "newick_meta"]

    # config
    policy_function = PolicyFunction(policy_config=policy_config)
    if tree_config.evaluation_type == 'gcn':
        value_function = ValueFunction(weights_path=value_weights_path)
    else:
        value_function = None

    # run search
    n_solved = 0
    extracted_paths = []
    with MoleculeReader(targets_file) as targets_path, open(stats_file, "w", newline="\n") as csvfile:
        statswriter = csv.DictWriter(csvfile, delimiter=",", fieldnames=stats_header)
        statswriter.writeheader()

        for ti, target in tqdm(enumerate(targets_path), total=len(targets_path)):

            try:
                # run search
                tree = Tree(
                    target=target,
                    tree_config=tree_config,
                    reaction_rules_path=reaction_rules_path,
                    building_blocks_path=building_blocks_path,
                    policy_function=policy_function,
                    value_function=value_function,
                )
                _ = list(tree)

            except:
                continue

            n_solved += bool(tree.winning_nodes)

            # extract routes
            extracted_paths.append(extract_routes(tree))

            # retropaths
            retropaths_file = retropaths_folder.joinpath(f"retropaths_target_{ti}.html")
            to_table(tree, retropaths_file, extended=True)

            # stats
            statswriter.writerow(extract_tree_stats(tree, target))
            csvfile.flush()

            #
            with open(paths_file, 'w') as f:
                json.dump(extracted_paths, f)

    print(f"Solved number of target molecules: {n_solved}")

