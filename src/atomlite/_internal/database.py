import collections
import json
import pathlib
import sqlite3
import typing

from atomlite._internal.json import Entry, Molecule

DatabaseGetMolecules: typing.TypeAlias = collections.abc.Iterator[
    tuple[str, Molecule]
]


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
