"""
Module for the preparation and training of a policy network used in the expansion of nodes in tree search.
This module includes functions for creating training datasets and running the training process for the policy network.
"""

import warnings
from pathlib import Path

import torch
from pytorch_lightning import Trainer
from torch.utils.data import random_split
from torch_geometric.data.lightning import LightningDataset

from SynTool.ml.networks.policy import PolicyNetwork
from SynTool.utils.config import PolicyNetworkConfig
from SynTool.ml.training.preprocessing import RankingPolicyDataset, FilteringPolicyDataset
from SynTool.utils.logging import DisableLogger

warnings.filterwarnings("ignore")


def create_policy_dataset(reaction_rules_path: str,
                          molecules_or_reactions_path: str,
                          output_path: str,
                          dataset_type: str = "filtering",
                          batch_size: int = 100,
                          num_cpus: int = 1,
                          training_data_ratio: float = 0.8):
    """
    Create a training dataset for a policy network.

    :param reaction_rules_path: Path to the reaction rules file.
    :param molecules_or_reactions_path: Path to the molecules or reactions file used to create the training set.
    :param output_path: Path to store the processed dataset.
    :param dataset_type: Type of the dataset to be created ('ranking' or 'filtering').
    :param batch_size: The size of batch of molecules/reactions.
    :param training_data_ratio: Ratio of training data to total data.
    :param num_cpus: Number of CPUs to use for data processing.

    :return: A `LightningDataset` object containing training and validation datasets.
    """
    with DisableLogger():
        if dataset_type == "filtering":
            full_dataset = FilteringPolicyDataset(
                reaction_rules_path=reaction_rules_path,
                molecules_path=molecules_or_reactions_path,
                output_path=output_path,
                num_cpus=num_cpus)

        elif dataset_type == "ranking":
            full_dataset = RankingPolicyDataset(
                reaction_rules_path=reaction_rules_path,
                reactions_path=molecules_or_reactions_path,
                output_path=output_path)

    train_size = int(training_data_ratio * len(full_dataset))
    val_size = len(full_dataset) - train_size

    train_dataset, val_dataset = random_split(full_dataset, [train_size, val_size], torch.Generator().manual_seed(42))
    print(f"Training set size: {len(train_dataset)}, validation set size: {len(val_dataset)}")

    datamodule = LightningDataset(
        train_dataset,
        val_dataset,
        batch_size=batch_size,
        pin_memory=True,
        drop_last=True)

    return datamodule


def run_policy_training(datamodule: LightningDataset,
                        config: PolicyNetworkConfig,
                        results_path: str,
                        accelerator: str = "gpu") -> None:

    """
    Trains a policy network using a given datamodule and training configuration.

    :param datamodule: A PyTorch Lightning `DataModule` class instance. It is responsible for
     loading, processing, and preparing the training data for the model.
    :param config: The dictionary that contains various configuration settings for the policy training process.
    :param results_path: Path to store the training results and logs.
    :param accelerator: The type of hardware accelerator to use for training (e.g., 'gpu', 'cpu'). Defaults to "gpu".

    :return: None.
    """
    results_path = Path(results_path)
    results_path.mkdir(exist_ok=True)

    weights_path = results_path.joinpath("policy_network.ckpt")

    network = PolicyNetwork(
        vector_dim=config.vector_dim,
        n_rules=datamodule.train_dataset.dataset.num_classes,
        batch_size=config.batch_size,
        dropout=config.dropout,
        num_conv_layers=config.num_conv_layers,
        learning_rate=config.learning_rate,
        policy_type=config.policy_type)

    trainer = Trainer(
        accelerator=accelerator,
        devices=[0],
        max_epochs=config.num_epoch,
        logger=False,
        gradient_clip_val=1.0,
        enable_progress_bar=True)

    trainer.fit(network, datamodule)
    ba = round(trainer.logged_metrics['train_balanced_accuracy_y_step'].item(), 3)
    trainer.save_checkpoint(weights_path)

    print(f'Policy network balanced accuracy: {ba}')


