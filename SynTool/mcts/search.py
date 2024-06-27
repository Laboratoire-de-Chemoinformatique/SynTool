"""Module containing functions for running tree search for the set of target
molecules."""

import csv
import json
import os.path
from pathlib import Path

from CGRtools import smiles
from tqdm import tqdm

from SynTool.mcts.evaluation import ValueNetworkFunction
from SynTool.mcts.expansion import PolicyNetworkFunction
from SynTool.mcts.tree import Tree, TreeConfig
from SynTool.utils.config import PolicyNetworkConfig
from SynTool.utils.loading import load_building_blocks, load_reaction_rules
from SynTool.utils.visualisation import extract_routes, generate_results_html


def extract_tree_stats(tree, target):
    """Collects various statistics from a tree and returns them in a dictionary
    format.

    :param tree: The built search tree.
    :param target: The target molecule associated with the tree.
    :return: A dictionary with the calculated statistics.
    """

    if isinstance(target, str):
        target_smi = target
        target = smiles(target)
        target.meta["init_smiles"] = target_smi

    newick_tree, newick_meta = tree.newickify(visits_threshold=0)
    newick_meta_line = ";".join(
        [f"{nid},{v[0]},{v[1]},{v[2]}" for nid, v in newick_meta.items()]
    )

    if len(tree.winning_nodes) > 0:
        debug = "IS_SOLVED"
    else:
        debug = "NOT_SOLVED"

    return {
        "target_smiles": target.meta["init_smiles"],
        "num_routes": len(tree.winning_nodes),
        "num_nodes": len(tree),
        "num_iter": tree.curr_iteration,
        "search_time": round(tree.curr_time, 1),
        "newick_tree": newick_tree,
        "newick_meta": newick_meta_line,
        "debug_info": debug,
    }


def run_search(
    targets_path: str,
    search_config: dict,
    policy_config: PolicyNetworkConfig,
    reaction_rules_path: str,
    building_blocks_path: str,
    value_network_path: str = None,
    results_root: str = "search_results",
) -> None:
    """Performs a tree search on a set of target molecules using specified
    configuration and reaction rules, logging the results and statistics.

    :param targets_path: The path to the file containing the target
        molecules (in SDF or SMILES format).
    :param search_config: The config object containing the configuration
        for the tree search.
    :param policy_config: The config object containing the configuration
        for the policy.
    :param reaction_rules_path: The path to the file containing reaction
        rules.
    :param building_blocks_path: The path to the file containing
        building blocks.
    :param value_network_path: The path to the file containing value
        weights (optional).
    :param results_root: The name of the folder where the results of the
        tree search will be saved.
    :return: None.
    """

    # results folder
    results_root = Path(results_root)
    if not results_root.exists():
        results_root.mkdir()

    # output files
    stats_file = results_root.joinpath("tree_search_stats.csv")
    routes_file = results_root.joinpath("extracted_routes.json")
    routes_folder = results_root.joinpath("extracted_routes_html")
    routes_folder.mkdir(exist_ok=True)

    # stats header
    stats_header = [
        "target_smiles",
        "num_routes",
        "num_nodes",
        "num_iter",
        "search_time",
        "newick_tree",
        "newick_meta",
        "debug_info",
    ]

    # config
    policy_function = PolicyNetworkFunction(policy_config=policy_config)
    if search_config["evaluation_type"] == "gcn" and value_network_path:
        value_function = ValueNetworkFunction(weights_path=value_network_path)
    else:
        value_function = None

    reaction_rules = load_reaction_rules(reaction_rules_path)
    building_blocks = load_building_blocks(building_blocks_path)

    # run search
    n_solved = 0
    extracted_routes = []

    tree_config = TreeConfig.from_dict(search_config)
    tree_config.silent = True
    with open(targets_path, "r", encoding="utf-8") as targets, open(
        stats_file, "w", encoding="utf-8", newline="\n"
    ) as csvfile:

        statswriter = csv.DictWriter(csvfile, delimiter=",", fieldnames=stats_header)
        statswriter.writeheader()

        for ti, target_smi in tqdm(
            enumerate(targets),
            leave=True,
            desc="Number of target molecules processed: ",
            bar_format="{desc}{n} [{elapsed}]",
        ):
            target_smi = target_smi.strip()
            try:
                # run search
                tree = Tree(
                    target=target_smi,
                    config=tree_config,
                    reaction_rules=reaction_rules,
                    building_blocks=building_blocks,
                    expansion_function=policy_function,
                    evaluation_function=value_function,
                )

                _ = list(tree)

            except Exception as e:
                extracted_routes.append(
                    [
                        {
                            "type": "mol",
                            "smiles": target_smi,
                            "in_stock": False,
                            "children": [],
                        }
                    ]
                )
                statswriter.writerow({"target_smiles": target_smi, "debug_info": e})

                csvfile.flush()
                continue

            # is solved
            n_solved += bool(tree.winning_nodes)

            # extract routes
            extracted_routes.append(extract_routes(tree))

            # save routes
            generate_results_html(
                tree,
                os.path.join(routes_folder, f"retroroutes_target_{ti}.html"),
                extended=True,
            )

            # save stats
            statswriter.writerow(extract_tree_stats(tree, target_smi))
            csvfile.flush()

            # save json routes
            with open(routes_file, "w", encoding="utf-8") as f:
                json.dump(extracted_routes, f)

    print(f"Number of solved target molecules: {n_solved}")
