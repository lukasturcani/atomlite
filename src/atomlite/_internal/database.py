import collections
import json
import pathlib
import sqlite3
import typing
from dataclasses import asdict, dataclass, field

import rdkit.Chem as rdkit

from atomlite._internal.json import Json, Molecule, json_from_rdkit

Properties: typing.TypeAlias = dict[str, Json] | None
DatabaseGetMolecules: typing.TypeAlias = collections.abc.Iterator["Entry"]


@dataclass(frozen=True, slots=True)
class Entry:
    """
    A database entry.

    Parameters:
        key: Key used to uniquely identify the molecule.
        molecule: The molecule in JSON format.
        properties: User-defined molecular properties.
    """

    key: str
    """Key used to uniquely identify the molecule."""
    molecule: Molecule
    """The molecule in JSON format."""
    properties: "dict[str, Json]" = field(default_factory=dict)
    """User-defined molecular properties."""

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
        if properties is None:
            properties = {}
        return Entry(key, json_from_rdkit(molecule), properties)


def _entry_to_sqlite(entry: Entry) -> dict:
    d = asdict(entry)
    d["molecule"] = json.dumps(d["molecule"])
    d["properties"] = json.dumps(d["properties"])
    return d


@dataclass(frozen=True, slots=True)
class PropertyEntry:
    """
    A database property entry.

    Parameters:
        key: Key used to uniquely identify the molecule.
        properties: User-defined molecular properties.
    """

    key: str
    """Key used to uniquely identify the molecule."""
    properties: "dict[str, Json]"
    """User-defined molecular properties."""


def _property_entry_to_sqlite(entry: PropertyEntry) -> dict:
    d = asdict(entry)
    d["properties"] = json.dumps(d["properties"])
    return d


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
            "key TEXT PRIMARY KEY NOT NULL, "
            "molecule JSON NOT NULL, "
            "properties JSON NOT NULL)",
        )

    def add_entries(
        self,
        entries: Entry | collections.abc.Iterable[Entry],
    ) -> None:
        """
        Add molecular entries to the database.

        Parameters:
            entries (Entry | list[Entry]):
                The molecules to add to the database.
        """
        if isinstance(entries, Entry):
            entries = (entries,)

        self.connection.executemany(
            f"INSERT INTO {self._molecule_table} "
            "VALUES (:key, :molecule, :properties)",
            map(_entry_to_sqlite, entries),
        )

    def update_entries(
        self,
        entries: Entry | collections.abc.Iterable[Entry],
        merge_properties: bool = True,
    ) -> None:
        """
        Update molecules in the database.

        Parameters:
            entries (Entry | list[Entry]):
                The molecule entries to update in the database.
            merge_properties:
                If ``True``, the molecular properties will be
                merged rather than replaced. Properties present
                in both the update and the database will be
                overwritten.
        """
        if isinstance(entries, Entry):
            entries = (entries,)

        if merge_properties:
            self.connection.executemany(
                f"UPDATE {self._molecule_table} "
                "SET molecule=:molecule, "
                "properties=json_patch(properties,:properties) "
                "WHERE key=:key",
                map(_entry_to_sqlite, entries),
            )
        else:
            self.connection.executemany(
                f"UPDATE {self._molecule_table} "
                "SET molecule=:molecule, properties=:properties "
                "WHERE key=:key",
                map(_entry_to_sqlite, entries),
            )

    def get_entries(
        self,
        keys: str | collections.abc.Iterable[str] | None = None,
    ) -> "DatabaseGetMolecules":
        """
        Get molecular entries from the database.

        .. tip::

            The molecules returned from the database are in JSON
            format, you may need to convert them to something more
            usable, for example, :mod:`rdkit` molecules with
            :func:`.json_to_rdkit`.

        Parameters:
            keys (str | list[str] | None):
                The keys of the molecules to retrieve from the
                database. If ``None``, all entries will be returned.
        Yields:
            A molecular entry matching `keys`.
        """

        if keys is None:
            for key, molecule, properties in self.connection.execute(
                f"SELECT * FROM {self._molecule_table}",
            ):
                yield Entry(
                    key=key,
                    molecule=json.loads(molecule),
                    properties=json.loads(properties),
                )
            return

        if isinstance(keys, str):
            keys = (keys,)

        keys = tuple(keys)
        query = ",".join("?" * len(keys))
        for key, molecule, properties in self.connection.execute(
            f"SELECT * FROM {self._molecule_table} WHERE key IN ({query})",
            keys,
        ):
            yield Entry(
                key=key,
                molecule=json.loads(molecule),
                properties=json.loads(properties),
            )

    def update_properties(
        self,
        entries: PropertyEntry | collections.abc.Iterable[PropertyEntry],
        merge_properties: bool = True,
    ) -> None:
        """
        Update molecular properties.

        Parameters:
            entries (Entry | list[Entry]):
                The entries to update in the database.
            merge_properties:
                If ``True``, the molecular properties will be
                merged rather than replaced. Properties present
                in both the update and the database will be
                overwritten.
        """
        if isinstance(entries, PropertyEntry):
            entries = (entries,)

        if merge_properties:
            self.connection.executemany(
                f"UPDATE {self._molecule_table} "
                "SET properties=json_patch(properties,:properties) "
                "WHERE key=:key",
                map(_property_entry_to_sqlite, entries),
            )
        else:
            self.connection.executemany(
                f"UPDATE {self._molecule_table} "
                "SET properties=:properties "
                "WHERE key=:key",
                map(_property_entry_to_sqlite, entries),
            )
