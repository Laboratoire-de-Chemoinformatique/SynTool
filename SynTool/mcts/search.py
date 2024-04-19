"""
Module containing functions for running tree search for the set of target molecules.
"""

import csv
import json
import os.path
from pathlib import Path
from tqdm import tqdm
from CGRtools import smiles
from SynTool.interfaces.visualisation import generate_results_html, extract_routes
from SynTool.mcts.tree import Tree, TreeConfig
from SynTool.mcts.evaluation import ValueFunction
from SynTool.mcts.expansion import PolicyFunction
from SynTool.utils.config import PolicyNetworkConfig


def extract_tree_stats(tree, target):
    """
    Collects various statistics from a tree and returns them in a dictionary format.

    :param tree: The built search tree.
    :param target: The target molecule associated with the tree.

    :return: A dictionary with the calculated statistics.
    """

    if isinstance(target, str):
        target_smi = target
        target = smiles(target)
        target.meta['init_smiles'] = target_smi

    newick_tree, newick_meta = tree.newickify(visits_threshold=0)
    newick_meta_line = ";".join([f"{nid},{v[0]},{v[1]},{v[2]}" for nid, v in newick_meta.items()])

    if len(tree.winning_nodes) > 0:
        debug = 'SOLVED'
    else:
        debug = 'NOT SOLVED'

    return {"target_smiles": target.meta['init_smiles'],
            "tree_size": len(tree),
            "search_time": round(tree.curr_time, 1),
            "found_paths": len(tree.winning_nodes),
            "newick_tree": newick_tree,
            "newick_meta": newick_meta_line,
            "debug": debug}


def tree_search(
        targets_path: str,
        tree_config: TreeConfig,
        policy_config: PolicyNetworkConfig,
        reaction_rules_path: str,
        building_blocks_path: str,
        value_weights_path: str = None,
        results_root: str = "search_results") -> None:

    """
    Performs a tree search on a set of target molecules using specified configuration and reaction rules,
    logging the results and statistics.

    :param targets_path: The path to the file containing the target molecules (in SDF or SMILES format).
    :param tree_config: The config object containing the configuration for the tree search.
    :param policy_config: The config object containing the configuration for the policy.
    :param reaction_rules_path: The path to the file containing reaction rules.
    :param building_blocks_path: The path to the file containing building blocks.
    :param value_weights_path: The path to the file containing value weights (optional).
    :param results_root: The name of the folder where the results of the tree search will be saved.

    :return: None.
    """

    # results folder
    results_root = Path(results_root)
    if not results_root.exists():
        results_root.mkdir()

    # output files
    stats_file = results_root.joinpath("tree_search_stats.csv")
    paths_file = results_root.joinpath("extracted_routes.json")
    retropaths_folder = results_root.joinpath("extracted_routes")
    retropaths_folder.mkdir(exist_ok=True)

    # stats header
    stats_header = ["target_smiles", "tree_size", "search_time", "found_paths", "newick_tree", "newick_meta", "debug"]

    # config
    policy_function = PolicyFunction(policy_config=policy_config)
    if tree_config.evaluation_type == 'gcn':
        value_function = ValueFunction(weights_path=value_weights_path)
    else:
        value_function = None

    # run search
    n_solved = 0
    extracted_routes = []

    with open(targets_path, 'r') as targets, open(stats_file, "w", newline="\n") as csvfile:

        statswriter = csv.DictWriter(csvfile, delimiter=",", fieldnames=stats_header)
        statswriter.writeheader()

        for ti, target_smi in tqdm(enumerate(targets), leave=True, desc="Number of target molecules processed: ",
                                   bar_format='{desc}{n} [{elapsed}]'):
            target_smi = target_smi.strip()
            print(f'Search for {target_smi}')
            try:
                # run search
                tree = Tree(
                    target=target_smi,
                    tree_config=tree_config,
                    reaction_rules_path=reaction_rules_path,
                    building_blocks_path=building_blocks_path,
                    policy_function=policy_function,
                    value_function=value_function)

                _ = list(tree)

            except Exception as e:
                extracted_routes.append([{"type": "mol", "smiles": target_smi, "in_stock": False, "children": []}])
                statswriter.writerow({"target_smiles": target_smi,
                                      "tree_size": None,
                                      "search_time": None,
                                      "found_paths": None,
                                      "newick_tree": None,
                                      "newick_meta": None,
                                      "debug": e})
                csvfile.flush()
                continue

            # is solved
            n_solved += bool(tree.winning_nodes)

            # extract routes
            extracted_routes.append(extract_routes(tree))

            # write routes
            generate_results_html(tree, os.path.join(retropaths_folder, f"retropaths_target_{ti}.html"), extended=True)

            # write stats
            statswriter.writerow(extract_tree_stats(tree, target_smi))
            csvfile.flush()

            # write json routes
            with open(paths_file, 'w') as f:
                json.dump(extracted_routes, f)

    print(f"Solved number of target molecules: {n_solved}")

