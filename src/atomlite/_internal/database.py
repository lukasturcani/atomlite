import json
import pathlib
import sqlite3
import typing
from collections import abc

from atomlite._internal.json import Entry, Molecule


class Database:
    """
    A molecular SQLite database.

    Attributes:
        connection:
            An open database connection. Can be used to run
            SQL commands against the database.
    """

    connection: sqlite3.Connection

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

    def add_molecules(self, molecules: Entry | abc.Iterable[Entry]) -> None:
        """
        Add molecules to the database.

        Parameters:
            molecules (Entry | list[Entry]): The molecules to add to the database.

        """

        if isinstance(molecules, Entry):
            molecules = (molecules,)

        self.connection.executemany(
            f"INSERT INTO {self._molecule_table} VALUES (:key, :molecule)",
            molecules,
        )

    def get_molecules(
        self,
        keys: str | abc.Iterable[str],
    ) -> abc.Iterator[tuple[str, Molecule]]:
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
