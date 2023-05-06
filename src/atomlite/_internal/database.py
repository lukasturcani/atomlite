import collections
import json
import pathlib
import sqlite3
import typing

import rdkit.Chem as rdkit

from atomlite._internal.json import Json, Molecule, json_from_rdkit

DatabaseGetMolecules: typing.TypeAlias = collections.abc.Iterator[
    tuple[str, Molecule]
]
Properties: typing.TypeAlias = dict[str, Json] | None


class Entry(dict):
    """
    A database entry.
    """

    @staticmethod
    def from_rdkit(
        key: str,
        molecule: rdkit.Mol,
        properties: "Properties" = None,
    ) -> "Entry":
        """
        Create an :class:`.Entry` from an :mod:`rdkit` molecule.

        Parameters:
            key:
                The key used to uniquely identify the molecule
                in the database.
            molecule:
                The molecule.
            properties:
                Properties of the molecule as a JSON dictionary.

        Returns:
            The entry.
        """
        entry = Entry()
        entry["key"] = key
        entry["molecule"] = json.dumps(json_from_rdkit(molecule, properties))
        return entry

    @property
    def key(self) -> str:
        """The molecular key."""
        return self["key"]

    @property
    def molecule(self) -> Molecule:
        """The molecule."""
        return json.loads(self["molecule"])


class PropertyEntry(dict):
    """
    A database entry for a property JSON dictionary.
    """

    @property
    def key(self) -> str:
        """The molecular key."""
        return self["key"]

    @property
    def property(self) -> dict[str, Json]:
        """The property dictionary."""
        return self["property"]


class Database:
    """
    A molecular SQLite database.
    """

    connection: sqlite3.Connection
    """
    An open database connection.

    Can be used to run SQL commands against the database.
    """

    def __init__(
        self,
        database: pathlib.Path | str,
        molecule_table: typing.LiteralString = "molecules",
    ) -> None:
        """
        Parameters:
            database:
                The path to the database file.
            molecule_table:
                The name of the table which stores the molecules.
        """
        self._molecule_table = molecule_table
        self.connection = sqlite3.connect(database)
        self.connection.execute(
            f"CREATE TABLE IF NOT EXISTS {molecule_table}("
            "key TEXT PRIMARY KEY, molecule JSON)",
        )

    def add_molecules(
        self,
        molecules: Entry | collections.abc.Iterable[Entry],
    ) -> None:
        """
        Add molecules to the database.

        Parameters:
            molecules (Entry | list[Entry]):
                The molecules to add to the database.
        """
        if isinstance(molecules, Entry):
            molecules = (molecules,)

        self.connection.executemany(
            f"INSERT INTO {self._molecule_table} VALUES (:key, :molecule)",
            molecules,
        )

    def update_molecules(
        self,
        molecules: Entry | collections.abc.Iterable[Entry],
        merge_properties: bool = True,
    ) -> None:
        """
        Update molecules in the database.

        Parameters:
            molecules (Entry | list[Entry]):
                The molecule entries to update in the database.
            merge_properties:
                If ``True``, the molecular properties dictionary
                will not replace the existing one. Only fields
                which a present in both the update and the
                database will be replaced. If ``False``, the
                property dictionary of the update will completely
                replace any existing property dictionary in the
                database.
        """
        if isinstance(molecules, Entry):
            molecules = (molecules,)

        if merge_properties:
            raise NotImplementedError("")
        else:
            self.connection.executemany(
                f"UPDATE {self._molecule_table} "
                "SET molecule=:molecule WHERE key=:key",
                molecules,
            )

    def update_properties(
        self,
        properties: PropertyEntry | collections.abc.Iterable[PropertyEntry],
    ) -> None:
        raise NotImplementedError()

    def get_molecules(
        self,
        keys: str | collections.abc.Iterable[str],
    ) -> "DatabaseGetMolecules":
        """
        Get molecules from the database.

        .. tip::

            The molecules returned from the database are in JSON
            format, you may need to convert them to something more
            usable, for example, :mod:`rdkit` molecules with
            :func:`.json_to_rdkit`.

        Parameters:
            keys (str | list[str]):
                The keys of the molecules to retrieve from the
                database.

        Yields:
            The key and molecule. The molecule is in JSON format.
        """
        if isinstance(keys, str):
            keys = (keys,)

        keys = tuple(keys)
        query = ",".join("?" * len(keys))
        yield from (
            (key, json.loads(molecule_json_string))
            for key, molecule_json_string in self.connection.execute(
                f"SELECT * FROM {self._molecule_table} WHERE key IN ({query})",
                keys,
            )
        )
