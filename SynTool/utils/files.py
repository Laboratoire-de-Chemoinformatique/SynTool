from pathlib import Path
from os.path import splitext
from typing import Iterable, Union

from CGRtools import smiles
from CGRtools.containers import ReactionContainer, MoleculeContainer, CGRContainer, QueryContainer
from CGRtools.files.SDFrw import SDFRead, SDFWrite
from CGRtools.files.RDFrw import RDFRead, RDFWrite

from SynTool.utils import path_type


class SMILESRead:
    def __init__(self, filename: path_type, **kwargs):
        """
        Simplified class to read files containing a SMILES (Molecules or Reaction) string per line.
        :param filename: the path and name of the SMILES file to parse
        :return: None
        """
        filename = str(Path(filename).resolve(strict=True))
        self._file = open(filename, "r")
        self._data = self.__data()

        self._len = sum(1 for _ in open(filename, "r")) #TODO replace later

    def __data(self) -> Iterable[Union[ReactionContainer, CGRContainer]]:
        for line in iter(self._file.readline, ''):
            x = smiles(line)
            if isinstance(x, (ReactionContainer, CGRContainer, MoleculeContainer)):
                yield x

    def __enter__(self):
        return self

    def read(self):
        """
        Parse whole SMILES file.

        :return: List of parsed molecules or reactions.
        """
        return list(iter(self))

    def __iter__(self):
        return (x for x in self._data)

    def __next__(self):
        return next(iter(self))

    def __len__(self):
        return self._len

    def close(self):
        self._file.close()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class FileHandler:
    def __init__(self, filename: path_type, **kwargs):
        """
        General class to handle chemical files.

        :param filename: the path and name of the file
        :type filename: path_type

        :return: None
        """
        self._file = None
        # filename = str(Path(filename).resolve(strict=True)) #TODO Tagir please correct bug in ReactionWriter following your modification
        _, ext = splitext(filename)
        file_types = {
            '.smi': "SMI",
            '.smiles': "SMI",
            '.rdf': "RDF",
            '.sdf': 'SDF',
        }
        try:
            self._file_type = file_types[ext]
        except KeyError:
            raise ValueError("I don't know the file extension,", ext)

    def close(self):
        self._file.close()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class Reader(FileHandler):
    def __init__(self, filename: path_type, **kwargs):
        """
        General class to read chemical files.

        :param filename: the path and name of the file
        :type filename: path_type

        :return: None
        """
        super().__init__(filename, **kwargs)

    def __enter__(self):
        return self._file

    def __iter__(self):
        return iter(self._file)

    def __next__(self):
        return next(self._file)


class Writer(FileHandler):
    def __init__(self, filename: path_type, mapping: bool = True, **kwargs):
        """
        General class to write chemical files.

        :param filename: the path and name of the file
        :type filename: path_type

        :param mapping: whenever to save mapping or not
        :type mapping: bool

        :return: None
        """
        super().__init__(filename, **kwargs)
        self._mapping = mapping

    def __enter__(self):
        return self


class ReactionReader(Reader):
    def __init__(self, filename: path_type, **kwargs):
        """
        Class to read reaction files.

        :param filename: the path and name of the file
        :type filename: path_type

        :return: None
        """
        super().__init__(filename, **kwargs)
        if self._file_type == "SMI":
            self._file = SMILESRead(filename, **kwargs)
        elif self._file_type == "RDF":
            self._file = RDFRead(filename, indexable=True, **kwargs)
        else:
            raise ValueError("File type incompatible -", filename)


class ReactionWriter(Writer):
    def __init__(self, filename: path_type, append_results: bool = False, mapping: bool = True, **kwargs):
        """
        Class to write reaction files.

        :param filename: the path and name of the file
        :type filename: path_type

        :param append_results: whenever to append the new reactions (True) or to override the file (False)
        :type append_results: bool

        :param mapping: whenever to save mapping or not
        :type mapping: bool

        :return: None
        """
        super().__init__(filename, mapping, **kwargs)
        if self._file_type == "SMI":
            open_mode = "a" if append_results else "w"
            self._file = open(filename, open_mode, **kwargs)
        elif self._file_type == "RDF":
            self._file = RDFWrite(filename, append=append_results, **kwargs)
        else:
            raise ValueError("File type incompatible -", filename)

    def write(self, reaction: ReactionContainer):
        """
        Function to write a specific reaction to the file.

        :param reaction: the path and name of the file
        :type reaction: ReactionContainer

        :return: None
        """
        if self._file_type == "SMI":
            rea_str = format(reaction, "m") if self._mapping else str(reaction)
            self._file.write(rea_str + "\n")
        elif self._file_type == "RDF":
            self._file.write(reaction)


class MoleculeReader(Reader):
    def __init__(self, filename: path_type, **kwargs):
        """
        Class to read molecule files.

        :param filename: the path and name of the file

        :return: None
        """
        super().__init__(filename, **kwargs)
        if self._file_type == "SMI":
            self._file = SMILESRead(filename, ignore=True, **kwargs)
        elif self._file_type == "SDF":
            self._file = SDFRead(filename, indexable=True, **kwargs)
        else:
            raise ValueError("File type incompatible -", filename)


class MoleculeWriter(Writer):
    def __init__(self, filename: path_type, append_results: bool = False, mapping: bool = True, **kwargs):
        """
        Class to write molecule files.

        :param filename: the path and name of the file
        :type filename: path_type

        :param append_results: whenever to append the new molecules (True) or to override the file (False)
        :type append_results: bool

        :param mapping: whenever to save mapping or not
        :type mapping: bool

        :return: None
        """
        super().__init__(filename, mapping, **kwargs)
        if self._file_type == "SMI":
            open_mode = "a" if append_results else "w"
            self._file = open(filename, open_mode, **kwargs)
        elif self._file_type == "SDF":
            self._file = SDFWrite(filename, append=append_results, **kwargs)
        else:
            raise ValueError("File type incompatible -", filename)

    def write(self, molecule):
        """
        Function to write a specific molecule to the file.

        :param molecule: the path and name of the file
        :type molecule: MoleculeContainer | CGRContainer | QueryContainer

        :return: None
        """
        if self._file_type == "SMI":
            mol_str = format(molecule, "m") if self._mapping else str(molecule)
            self._file.write(mol_str + "\n")
        elif self._file_type == "SDF":
            self._file.write(molecule)
