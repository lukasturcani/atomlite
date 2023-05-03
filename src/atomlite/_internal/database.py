import json
import pathlib
import sqlite3
import typing

from atomlite._internal.json import Entry, Molecule


class Database:
    connection: sqlite3.Connection

    def __init__(
        self,
        database: pathlib.Path | str,
        molecule_table: typing.LiteralString = "molecules",
    ) -> None:
        self._molecule_table = molecule_table
        self.connection = sqlite3.connect(database)
        self.connection.execute(
            f"CREATE TABLE IF NOT EXISTS {molecule_table}("
            "key TEXT PRIMARY KEY, molecule JSON)",
        )

    def add_molecules(self, molecules: Entry | typing.Iterable[Entry]) -> None:
        if isinstance(molecules, Entry):
            molecules = (molecules,)

        self.connection.executemany(
            f"INSERT INTO {self._molecule_table} VALUES (:key, :molecule)",
            molecules,
        )

    def get_molecules(
        self,
        keys: str | typing.Iterable[str],
    ) -> typing.Iterator[tuple[str, Molecule]]:
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
