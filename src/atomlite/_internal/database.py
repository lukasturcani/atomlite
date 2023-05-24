import collections
import json
import pathlib
import sqlite3
import typing
from dataclasses import asdict, dataclass, field

import rdkit.Chem as rdkit

from atomlite._internal.json import Json, Molecule, json_from_rdkit

Properties: typing.TypeAlias = dict[str, Json] | None


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


class MoleculeNotFound(Exception):
    """
    Raised when a molecule is not found in the database.
    """

    pass


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
        commit: bool = True,
    ) -> None:
        """
        Add molecular entries to the database.

        Parameters:
            entries (Entry | list[Entry]):
                The molecules to add to the database.
            commit:
                If ``True`` changes will be automatically
                commited to the database file.
        """
        if isinstance(entries, Entry):
            entries = (entries,)

        self.connection.executemany(
            f"INSERT INTO {self._molecule_table} "
            "VALUES (:key, :molecule, :properties)",
            map(_entry_to_sqlite, entries),
        )
        if commit:
            self.connection.commit()

    def update_entries(
        self,
        entries: Entry | collections.abc.Iterable[Entry],
        merge_properties: bool = True,
        commit: bool = True,
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
            commit:
                If ``True`` changes will be automatically
                commited to the database file.
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
        if commit:
            self.connection.commit()

    def get_entries(
        self,
        keys: str | collections.abc.Iterable[str] | None = None,
    ) -> collections.abc.Iterator[Entry]:
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

    def get_property(
        self,
        key: str,
        path: str,
    ) -> "Json":
        """
        Get the property of a molecule.

        .. note::

            If `path` does not lead to a property which exists,
            ``None`` will be returned. This means that the same
            value is returned for a missing value as well as an
            exisiting value set to ``None``. If you need to
            distinguish between missing and ``None`` values you
            can use a different value to represent missing data,
            for example the string ``"MISSING"``.

        Parameters:
            key: The key of the molecule.
            path:
                A path to the property of the molecule. Valid
                paths are described here_. You can also view various
                code :ref:`examples<examples-valid-property-paths>`
                in our docs.
        Returns:
            The property.
        Raises:
            MoleculeNotFound:
                If the molecule is not found in the database.

        .. _here: https://www.sqlite.org/json1.html#path_arguments
        """
        result = self.connection.execute(
            "SELECT json_extract(properties,?), "
            "json_type(properties,?) "
            f"FROM {self._molecule_table} "
            "WHERE key=?",
            (path, path, key),
        ).fetchone()
        if result is None:
            raise MoleculeNotFound(
                "Can't get property of a molecule not in the database."
            )
        property, property_type = result
        if property_type == "object" or property_type == "array":
            return json.loads(property)
        elif property_type == "true" or property_type == "false":
            return bool(property)
        else:
            return property

    def set_property(
        self,
        key: str,
        path: str,
        property: float | str | bool | None,
        commit: bool = True,
    ) -> None:
        """
        Set the property of molecule.

        .. note::

            If `key` does not exist in the database, this function
            will finish successfully but it will not change the database.

        Parameters:
            key:
                The key of the molecule.
            path:
                A path to the property of the molecule. Valid
                paths are described here_. You can also view various
                code :ref:`examples<examples-valid-property-paths>`
                in our docs.
            property:
                The desired value of the property.
            commit:
                If ``True`` changes will be automatically
                commited to the database file.
        """
        self.connection.execute(
            f"UPDATE {self._molecule_table} "
            "SET properties=json_set(properties,?,?) "
            "WHERE key=?",
            (path, property, key),
        )

        if commit:
            self.connection.commit()

    def update_properties(
        self,
        entries: PropertyEntry | collections.abc.Iterable[PropertyEntry],
        merge_properties: bool = True,
        commit: bool = True,
    ) -> None:
        """
        Update molecular properties.

        Parameters:
            entries (PropertyEntry | list[PropertyEntry]):
                The entries to update in the database.
            merge_properties:
                If ``True``, the molecular properties will be
                merged rather than replaced. Properties present
                in both the update and the database will be
                overwritten.
            commit:
                If ``True`` changes will be automatically
                commited to the database file.
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
        if commit:
            self.connection.commit()
