"""Module containing a class Node in the tree search."""


class Node:
    """Node class represents a node in the tree search."""

    def __init__(
        self, retrons_to_expand: tuple = None, new_retrons: tuple = None
    ) -> None:
        """The function initializes the new Node object.

        :param retrons_to_expand: The tuple of retrons to be expanded. The first retron
            in the tuple is the current retron which will be expanded (for which new
            retrons will be generated by applying the predicted reaction rules). When
            the first retron has been successfully expanded, the second retron becomes
            the current retron to be expanded.
        :param new_retrons: The tuple of new retrons generated by applying the reaction
            rule.
        """

        self.retrons_to_expand = retrons_to_expand
        self.new_retrons = new_retrons

        if len(self.retrons_to_expand) == 0:
            self.curr_retron = tuple()
        else:
            self.curr_retron = self.retrons_to_expand[0]
            self.next_retrons = self.retrons_to_expand[1:]

    def __len__(self) -> int:
        """Returns the number of retrons in the node to expand."""
        return len(self.retrons_to_expand)

    def __repr__(self) -> str:
        """Returns the SMILES of each retron in retrons_to_expand and new_retrons."""
        return (
            f"Retrons to expand: {self.retrons_to_expand}\n"
            f"New retrons: {self.new_retrons}"
        )

    def is_solved(self) -> bool:
        """If True, it is a terminal node.

        There are not retrons for expansion.
        """

        return len(self.retrons_to_expand) == 0
