import pathlib
import sqlite3
import typing

import rdkit.Chem as rdkit


class Entry(dict):
    def __init__(self, key: str, molecule: rdkit.Mol) -> None:
        super().__init__()
        self["key"] = key
        self["molecule"] = molecule

    @property
    def key(self) -> str:
        return self["key"]

    @property
    def molecule(self) -> rdkit.Mol:
        return self["molecule"]


class Database:
    connection: sqlite3.Connection

    def __init__(
        self,
        database: pathlib.Path | str,
        molecule_table: typing.LiteralString = "molecules",
    ) -> None:
        self._molecule_table = molecule_table
        self.connection = sqlite3.connect(database)
        self.connection.enable_load_extension(True)
        self.connection.load_extension("chemicalite")
        self.connection.enable_load_extension(False)

        self.connection.execute(
            f"CREATE TABLE IF NOT EXISTS {molecule_table}("
            "key TEXT PRIMARY KEY, molecule MOL)",
        )

    def add_molecules(self, molecules: Entry | typing.Iterable[Entry]) -> None:
        if isinstance(molecules, Entry):
            molecules = (molecules,)

        self.connection.executemany(
            f"INSERT INTO {self._molecule_table} VALUES (:key, :molecule)",
            molecules,
        )

    def get_molecules(
        self, keys: str | typing.Iterable[str]
    ) -> typing.Iterator[Entry]:
        if isinstance(keys, str):
            keys = (keys,)
