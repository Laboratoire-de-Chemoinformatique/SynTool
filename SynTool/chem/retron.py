"""Module containing a class Retron that represents a retron (extend molecule object) in
the search tree."""

from typing import Set

from CGRtools.containers import MoleculeContainer

from SynTool.chem.utils import safe_canonicalization


class Retron:
    """Retron class is used to extend the molecule behavior needed for interaction with
    a tree in MCTS."""

    def __init__(self, molecule: MoleculeContainer):
        """It initializes a Retron object with a molecule container as a parameter.

        :param molecule: A molecule.
        """
        self.molecule = safe_canonicalization(molecule)
        self.prev_retrons = []

    def __len__(self) -> int:
        """Return the number of atoms in Retron."""
        return len(self.molecule)

    def __hash__(self) -> hash:
        """Returns the hash value of Retron."""
        return hash(self.molecule)

    def __str__(self) -> str:
        """Returns a SMILES of the Retron."""
        return str(self.molecule)

    def __eq__(self, other: "Retron") -> bool:
        """Checks if the current Retron is equal to another Retron."""
        return self.molecule == other.molecule

    def __repr__(self) -> str:
        """Returns a SMILES of the Retron."""
        return str(self.molecule)

    def is_building_block(self, bb_stock: Set, min_mol_size: int = 6) -> bool:
        """Checks if a Retron is a building block.

        :param bb_stock: The list of building blocks. Each building block is represented
            by a canonical SMILES.
        :param min_mol_size: If the size of the Retron is equal or smaller than
            min_mol_size it is automatically classified as building block.
        :return: True is Retron is a building block.
        """
        if len(self.molecule) <= min_mol_size:
            return True

        return str(self.molecule) in bb_stock


def retrons_to_cgr(
    retrons: list = None, exclude_small: bool = True, min_mol_size: int = 6
) -> MoleculeContainer:
    """Takes a list of retrons, excludes small retrons if specified, and composes them
    into a single molecule. The composed molecule then is used for the prediction of
    synthesisability of the characterizing the possible success of the route including
    the nodes with the given retrons.

    :param retrons: The list of retrons to be composed.
    :param exclude_small: The parameter that determines whether small retrons should be excluded from the composition
    process. If `exclude_small` is set to `True`, only retrons with a length greater than min_mol_size will be composed.
    :param min_mol_size: The parameter used with exclude_small.

    :return: A composed retrons as a MoleculeContainer object.
    """

    if len(retrons) == 1:
        return retrons[0].molecule
    if len(retrons) > 1:
        if exclude_small:
            big_retrons = [
                retron for retron in retrons if len(retron.molecule) > min_mol_size
            ]
            if big_retrons:
                retrons = big_retrons
        tmp_mol = retrons[0].molecule.copy()
        transition_mapping = {}
        for mol in retrons[1:]:
            for n, atom in mol.molecule.atoms():
                new_number = tmp_mol.add_atom(atom.atomic_symbol)
                transition_mapping[n] = new_number
            for atom, neighbor, bond in mol.molecule.bonds():
                tmp_mol.add_bond(
                    transition_mapping[atom], transition_mapping[neighbor], bond
                )
            transition_mapping = {}

        return tmp_mol
