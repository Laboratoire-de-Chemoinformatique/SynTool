"""
Module for preparation of the training set and training of the policy network used for nodes expansion in MCTS
"""

import os.path as osp
import warnings

import torch
from pytorch_lightning import Trainer
from pytorch_lightning.callbacks import LearningRateMonitor, ModelCheckpoint
from pytorch_lightning.loggers import CSVLogger
from torch.utils.data import random_split
from torch_geometric.data.lightning import LightningDataset

from Synto.ml.networks.policy import PolicyNetwork
from Synto.ml.training.preprocessing import FilteringPolicyDataset
from Synto.chem.loading import load_reaction_rules
from Synto.utils.logging import DisableLogger, HiddenPrints

warnings.filterwarnings('ignore')


def create_policy_training_set(reaction_rules_path=None,
                               molecules_path=None,
                               output_path=None,
                               batch_size=None,
                               num_cpus=None):
    """
    Creates a training set for a policy network using a given configuration. Configuration dictionary specifies the path
    to the extracted reaction rules and molecules for generating the training set. Each reaction rule is applied to the
    given training molecule resulting in the final labels vector. The length of the final rule appliance vector is equal
    to the number of rules. The 1 in this vector corresponds to the successfully applied reaction rules and 0 to the not
    applicable reaction rules. Each training molecule is encoded with atom/bonds vectors and stored as PyTorch Geometric
    graphs.

    :param num_cpus:
    :param batch_size:
    :param output_path:
    :param molecules_path:
    :param reaction_rules_path:
    :return: A `LightningDataset` object containing PyTorch Geometric graphs for training molecules and label vectors.
    """
    #
    with DisableLogger() as DL:
        full_dataset = FilteringPolicyDataset(molecules_path=molecules_path,
                                              reaction_rules_path=reaction_rules_path,
                                              output_path=output_path,
                                              num_cpus=num_cpus)

    train_size = int(0.8 * len(full_dataset))
    val_size = len(full_dataset) - train_size

    train_dataset, val_dataset = random_split(full_dataset, [train_size, val_size], torch.Generator().manual_seed(42))
    print(f'Training set size: {len(train_dataset)}, validation set size: {len(val_dataset)}')
    #
    datamodule = LightningDataset(train_dataset, val_dataset, batch_size=batch_size, pin_memory=True)

    return datamodule


def run_policy_training(datamodule, config, n_rules=None, results_path=None):
    """
    Trains a policy network using a given datamodule and training configuration.

    :param results_path:
    :param n_rules:
    :param datamodule: The PyTorch Lightning `DataModule` class. It is responsible for loading and preparing the
    training data for the model.
    :param config: The dictionary that contains various configuration settings (path to the reaction rules file, vector
    dimension, batch size, dropout rate, number of convolutional layers, learning rate, number of epochs, etc.) for the
    policy training process.
    """
    #
    network = PolicyNetwork(vector_dim=config['PolicyNetwork']['vector_dim'], n_rules=n_rules,
                            batch_size=config['PolicyNetwork']['batch_size'],
                            dropout=config['PolicyNetwork']['dropout'],
                            num_conv_layers=config['PolicyNetwork']['num_conv_layers'],
                            learning_rate=config['PolicyNetwork']['learning_rate'])
    #
    weights_path = osp.join(results_path)
    logs_path = osp.join(results_path)

    lr_monitor = LearningRateMonitor(logging_interval='epoch')
    logger = CSVLogger(logs_path)

    checkpoint = ModelCheckpoint(dirpath=weights_path, filename='policy_network', monitor="val_loss", mode="min")
    #
    with DisableLogger() as DL, HiddenPrints() as HP:
        trainer = Trainer(accelerator='gpu', devices=[0], max_epochs=config['PolicyNetwork']['num_epoch'],
                          callbacks=[lr_monitor, checkpoint], logger=logger, gradient_clip_val=1.0,
                          enable_progress_bar=False)

        trainer.fit(network, datamodule)

    ba = round(trainer.logged_metrics['train_balanced_accuracy_y_step'].item(), 3)
    print(f'Policy network balanced accuracy: {ba}')
