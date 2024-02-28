import collections
import json
import pathlib
import sqlite3
import typing
from collections import defaultdict
from dataclasses import dataclass, field

import polars as pl
import rdkit.Chem as rdkit  # noqa: N813

from atomlite._internal.json import Json, Molecule, json_from_rdkit

Properties: typing.TypeAlias = dict[str, Json] | None


@dataclass(frozen=True, slots=True)
class Entry:
    """A database entry.

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
        """Create an :class:`.Entry` from an :mod:`rdkit` molecule.

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


def _entry_to_sqlite(entry: Entry) -> dict[str, Json]:
    return {
        "key": entry.key,
        "molecule": json.dumps(entry.molecule),
        "properties": json.dumps(entry.properties),
    }


@dataclass(frozen=True, slots=True)
class PropertyEntry:
    """A database property entry.

    Parameters:
        key: Key used to uniquely identify the molecule.
        properties: User-defined molecular properties.
    """

    key: str
    """Key used to uniquely identify the molecule."""
    properties: "dict[str, Json]"
    """User-defined molecular properties."""


def _property_entry_to_sqlite(entry: PropertyEntry) -> dict[str, Json]:
    return {
        "key": entry.key,
        "properties": json.dumps(entry.properties),
    }


class Database:
    """A molecular SQLite database.

    Parameters:
        database:
            The path to the database file.
        molecule_table:
            The name of the table which stores the molecules.
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
        self._molecule_table = molecule_table
        self.connection = sqlite3.connect(database)
        self.connection.execute(
            f"CREATE TABLE IF NOT EXISTS {molecule_table}("
            "key TEXT PRIMARY KEY NOT NULL, "
            "molecule JSON, "
            "properties JSON NOT NULL)",
        )

    def num_entries(self) -> int:
        """Get the number of molecular entries in the database.

        .. note::

            This number includes both the commited and
            uncommited entries.
        """
        return self.connection.execute(
            f"SELECT COUNT(*) FROM {self._molecule_table} "  # noqa: S608
            "WHERE molecule IS NOT NULL",
        ).fetchone()[0]

    def num_property_entries(self) -> int:
        """Get the number of property entries in the database.

        .. note::

            This number includes both the commited and
            uncommited entries.
        """
        return self.connection.execute(
            f"SELECT COUNT(*) FROM {self._molecule_table}"  # noqa: S608
        ).fetchone()[0]

    def add_entries(
        self,
        entries: Entry | collections.abc.Iterable[Entry],
        *,
        commit: bool = True,
    ) -> None:
        """Add molecular entries to the database.

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
            f"INSERT INTO {self._molecule_table} "  # noqa: S608
            "VALUES (:key, :molecule, :properties)",
            map(_entry_to_sqlite, entries),
        )
        if commit:
            self.connection.commit()

    def remove_entries(
        self,
        keys: str | collections.abc.Iterable[str],
        *,
        commit: bool = True,
    ) -> None:
        """Remove molecular entries from the database.

        Parameters:
            keys: The keys of the molecules to remove from the database.
            commit:
                If ``True`` changes will be automatically
                commited to the database file.
        """
        if isinstance(keys, str):
            keys = (keys,)
        self.connection.executemany(
            f"DELETE FROM {self._molecule_table} "  # noqa: S608
            "WHERE key=?",
            ((key,) for key in keys),
        )
        if commit:
            self.connection.commit()

    def update_entries(
        self,
        entries: Entry | collections.abc.Iterable[Entry],
        *,
        merge_properties: bool = True,
        upsert: bool = True,
        commit: bool = True,
    ) -> None:
        """Update molecular entries in the database.

        Parameters:
            entries (Entry | list[Entry]):
                The molecule entries to update in the database.
            merge_properties:
                If ``True``, the molecular properties will be
                merged rather than replaced. Properties present
                in both the update and the database will be
                overwritten.
            upsert:
                If ``True``, entries will be added to the
                database if missing.
            commit:
                If ``True`` changes will be automatically
                commited to the database file.
        """
        if isinstance(entries, Entry):
            entries = (entries,)

        if upsert:
            if merge_properties:
                self.connection.executemany(
                    f"INSERT INTO {self._molecule_table} "  # noqa: S608
                    "VALUES (:key, :molecule, :properties) "
                    "ON CONFLICT(key) DO UPDATE "
                    "SET molecule=:molecule, "
                    "properties=json_patch(properties,:properties) "
                    "WHERE key=:key",
                    map(_entry_to_sqlite, entries),
                )
            else:
                self.connection.executemany(
                    f"INSERT INTO {self._molecule_table} "  # noqa: S608
                    "VALUES (:key, :molecule, :properties) "
                    "ON CONFLICT(key) DO UPDATE "
                    "SET molecule=:molecule, properties=:properties "
                    "WHERE key=:key",
                    map(_entry_to_sqlite, entries),
                )
        else:  # noqa: PLR5501 - nested if statments are more readable
            if merge_properties:
                self.connection.executemany(
                    f"UPDATE {self._molecule_table} "  # noqa: S608
                    "SET molecule=:molecule, "
                    "properties=json_patch(properties,:properties) "
                    "WHERE key=:key",
                    map(_entry_to_sqlite, entries),
                )
            else:
                self.connection.executemany(
                    f"UPDATE {self._molecule_table} "  # noqa: S608
                    "SET molecule=:molecule, properties=:properties "
                    "WHERE key=:key",
                    map(_entry_to_sqlite, entries),
                )
        if commit:
            self.connection.commit()

    def has_entry(self, key: str) -> bool:
        """Check if a molecular entry is present in the database.

        Parameters:
            key: The key of the molecule to check.

        Returns:
            ``True`` if the entry is present in the database,
            ``False`` otherwise.
        """
        return (
            self.connection.execute(
                f"SELECT EXISTS(SELECT 1 FROM {self._molecule_table} "  # noqa: S608
                "WHERE key=? "
                "AND molecule IS NOT NULL "
                "LIMIT 1)",
                (key,),
            ).fetchone()[0]
            == 1
        )

    def has_property_entry(self, key: str) -> bool:
        """Check if a property entry is present in the database.

        Parameters:
            key: The key of the molecule to check.

        Returns:
            ``True`` if the entry is present in the database,
            ``False`` otherwise.
        """
        return (
            self.connection.execute(
                f"SELECT EXISTS(SELECT 1 FROM {self._molecule_table} "  # noqa: S608
                "WHERE key=? "
                "LIMIT 1)",
                (key,),
            ).fetchone()[0]
            == 1
        )

    def get_property_df(
        self,
        properties: collections.abc.Sequence[str],
        *,
        allow_missing: bool = False,
    ) -> pl.DataFrame:
        """Get a DataFrame of the properties in the database.

        Parameters:
            properties:
                The paths of the properties to retrieve.
                Valid paths are described
                `here <https://www.sqlite.org/json1.html#path_arguments>`_.
                You can also view various code
                :ref:`examples<examples-valid-property-paths>`
                in our docs.
            allow_missing:
                If ``True``, rows with some missing properties will be
                included in the DataFrame and hold ``null`` values.

        Returns:
            A DataFrame of the property entries in the database.
        """
        columns = []
        params = []
        wheres = []
        for i, prop in enumerate(properties):
            columns.append(
                f"json_extract(properties,?) AS prop{i},"
                f"json_type(properties,?) AS type{i}"
            )
            params.append(prop)
            params.append(prop)
            wheres.append(f"prop{i} IS NOT NULL")

        select = ",".join(columns)
        where = " OR ".join(wheres) if allow_missing else " AND ".join(wheres)

        data = defaultdict(list)
        for key, *property_results in self.connection.execute(
            f"SELECT key,{select} "  # noqa: S608
            f"FROM {self._molecule_table} "
            f"WHERE {where}",
            params,
        ):
            data["key"].append(key)
            for prop_name, prop_value, prop_type in _iter_props(
                properties, property_results
            ):
                if prop_type in {"object", "array"}:
                    data[prop_name].append(json.loads(prop_value))
                elif prop_type in {"true", "false"}:
                    data[prop_name].append(bool(prop_value))
                else:
                    data[prop_name].append(prop_value)
        return pl.DataFrame(data)

    def get_entry(self, key: str) -> Entry | None:
        """Get a molecular entry from the database.

        .. tip::

            The molecules returned from the database are in JSON
            format, you may need to convert them to something more
            usable, for example, :mod:`rdkit` molecules with
            :func:`.json_to_rdkit`.

        Parameters:
            key: The key of the molecule to retrieve from the database.

        Returns:
            The molecular entry matching `key` or ``None`` if
            `key` is not present in the database.

        See Also:
            * :meth:`.get_entries`: For retrieving multiple entries.
        """
        result = self.connection.execute(
            f"SELECT * FROM {self._molecule_table} "  # noqa: S608
            "WHERE key=? LIMIT 1",
            (key,),
        ).fetchone()
        if result is None:
            return None
        key, molecule, properties = result
        return Entry(
            key=key,
            molecule=json.loads(molecule),
            properties=json.loads(properties),
        )

    def get_entries(
        self,
        keys: str | collections.abc.Iterable[str] | None = None,
    ) -> collections.abc.Iterator[Entry]:
        """Get molecular entries from the database.

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

        See Also:
            * :meth:`.get_entry`: For retrieving a single entry.
        """
        if keys is None:
            for key, molecule, properties in self.connection.execute(
                f"SELECT * FROM {self._molecule_table} "  # noqa: S608
                "WHERE molecule IS NOT NULL",
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
            f"SELECT * FROM {self._molecule_table} WHERE key IN ({query})",  # noqa: S608
            keys,
        ):
            yield Entry(
                key=key,
                molecule=json.loads(molecule),
                properties=json.loads(properties),
            )

    def get_property_entry(self, key: str) -> PropertyEntry | None:
        """Get a property entry from the database.

        Parameters:
            key: The key of the molecule to retrieve from the database.

        Returns:
            The property entry matching `key` or ``None`` if
            `key` is not present in the database.

        See Also:
            * :meth:`.get_property_entries`: For retrieving multiple entries.
        """
        result = self.connection.execute(
            f"SELECT key,properties FROM {self._molecule_table} "  # noqa: S608
            "WHERE key=? LIMIT 1",
            (key,),
        ).fetchone()
        if result is None:
            return None
        key, properties = result
        return PropertyEntry(key=key, properties=json.loads(properties))

    def get_property_entries(
        self,
        keys: str | collections.abc.Iterable[str] | None = None,
    ) -> collections.abc.Iterator[PropertyEntry]:
        """Get property entries from the database.

        Parameters:
            keys (str | list[str] | None):
                The keys of the molecules to whose properties
                need to be retrieved from the database.
                If ``None`` all entries will be returned.

        Yields:
            A property entry matching `keys`.

        See Also:
            * :meth:`.get_property_entry`: For retrieving a single entry.
        """
        if keys is None:
            for key, properties in self.connection.execute(
                f"SELECT key,properties FROM {self._molecule_table}"  # noqa: S608
            ):
                yield PropertyEntry(key=key, properties=json.loads(properties))
            return

        if isinstance(keys, str):
            keys = (keys,)

        keys = tuple(keys)
        query = ",".join("?" * len(keys))
        for key, properties in self.connection.execute(
            f"SELECT key,properties FROM {self._molecule_table} "  # noqa: S608
            f"WHERE key IN ({query})",
            keys,
        ):
            yield PropertyEntry(key=key, properties=json.loads(properties))

    def get_bool_property(self, key: str, path: str) -> bool | None:
        """Get a boolean property of a molecule.

        Parameters:
            key:
                The key of the molecule.
            path:
                A path to the property of the molecule. Valid
                paths are described
                `here <https://www.sqlite.org/json1.html#path_arguments>`_.
                You can also view various code
                :ref:`examples<examples-valid-property-paths>`
                in our docs.

        Returns:
            The property. ``None`` will be returned if `key`
            is not present in the database or `path` leads to
            a non-existent property.

        Raises:
            TypeError: If the property is not a boolean.
        """
        result = self.connection.execute(
            "SELECT json_extract(properties,?), "  # noqa: S608
            "json_type(properties,?) "
            f"FROM {self._molecule_table} "
            "WHERE key=? LIMIT 1",
            (path, path, key),
        ).fetchone()
        if result is None:
            return None
        property_value, property_type = result
        if property_type is None:
            return None
        if property_type not in {"true", "false"}:
            msg = f"{property_type} property is not a bool: {property_value}"
            raise TypeError(msg)
        return bool(property_value)

    def set_bool_property(
        self,
        key: str,
        path: str,
        property: bool,  # noqa: A002, FBT001
        *,
        commit: bool = True,
    ) -> None:
        """Set a boolean property of a molecule.

        Parameters:
            key:
                The key of the molecule.
            path:
                A path to the property of the molecule. Valid
                paths are described
                `here <https://www.sqlite.org/json1.html#path_arguments>`_.
                You can also view various code
                :ref:`examples<examples-valid-property-paths>`
                in our docs.
            property:
                The desired value of the property.
            commit:
                If ``True`` changes will be automatically
                commited to the database file.
        """
        self.set_property(key, path, property, commit=commit)

    def get_int_property(self, key: str, path: str) -> int | None:
        """Get an integer property of a molecule.

        Parameters:
            key:
                The key of the molecule.
            path:
                A path to the property of the molecule. Valid
                paths are described
                `here <https://www.sqlite.org/json1.html#path_arguments>`_.
                You can also view various code
                :ref:`examples<examples-valid-property-paths>`
                in our docs.

        Returns:
            The property. ``None`` will be returned if `key`
            is not present in the database or `path` leads to
            a non-existent property.

        Raises:
            TypeError: If the property is not an integer.
        """
        result = self.connection.execute(
            "SELECT json_extract(properties,?), "  # noqa: S608
            "json_type(properties,?) "
            f"FROM {self._molecule_table} "
            "WHERE key=? LIMIT 1",
            (path, path, key),
        ).fetchone()
        if result is None:
            return None
        property_value, property_type = result
        if property_type is None:
            return None
        if property_type != "integer":
            msg = f"{property_type} property is not an int: {property_value}"
            raise TypeError(msg)
        return property_value

    def set_int_property(
        self,
        key: str,
        path: str,
        property: int,  # noqa: A002
        *,
        commit: bool = True,
    ) -> None:
        """Set an integer property of a molecule.

        Parameters:
            key:
                The key of the molecule.
            path:
                A path to the property of the molecule. Valid
                paths are described
                `here <https://www.sqlite.org/json1.html#path_arguments>`_.
                You can also view various code
                :ref:`examples<examples-valid-property-paths>`
                in our docs.
            property:
                The desired value of the property.
            commit:
                If ``True`` changes will be automatically
                commited to the database file.
        """
        self.set_property(key, path, property, commit=commit)

    def get_float_property(self, key: str, path: str) -> float | None:
        """Get a float property of a molecule.

        Parameters:
            key:
                The key of the molecule.
            path:
                A path to the property of the molecule. Valid
                paths are described
                `here <https://www.sqlite.org/json1.html#path_arguments>`_.
                You can also view various code
                :ref:`examples<examples-valid-property-paths>`
                in our docs.

        Returns:
            The property. ``None`` will be returned if `key`
            is not present in the database or `path` leads to
            a non-existent property.

        Raises:
            TypeError: If the property is not a float.
        """
        result = self.connection.execute(
            "SELECT json_extract(properties,?), "  # noqa: S608
            "json_type(properties,?) "
            f"FROM {self._molecule_table} "
            "WHERE key=? LIMIT 1",
            (path, path, key),
        ).fetchone()
        if result is None:
            return None
        property_value, property_type = result
        if property_type is None:
            return None
        if property_type != "real":
            msg = f"{property_type} property is not a float: {property_value}"
            raise TypeError(msg)
        return property_value

    def set_float_property(
        self,
        key: str,
        path: str,
        property: float,  # noqa: A002
        *,
        commit: bool = True,
    ) -> None:
        """Set a float property of a molecule.

        Parameters:
            key:
                The key of the molecule.
            path:
                A path to the property of the molecule. Valid
                paths are described
                `here <https://www.sqlite.org/json1.html#path_arguments>`_.
                You can also view various code
                :ref:`examples<examples-valid-property-paths>`
                in our docs.
            property:
                The desired value of the property.
            commit:
                If ``True`` changes will be automatically
                commited to the database file.
        """
        self.set_property(key, path, property, commit=commit)

    def get_str_property(self, key: str, path: str) -> str | None:
        """Get a string property of a molecule.

        Parameters:
            key:
                The key of the molecule.
            path:
                A path to the property of the molecule. Valid
                paths are described
                `here <https://www.sqlite.org/json1.html#path_arguments>`_.
                You can also view various code
                :ref:`examples<examples-valid-property-paths>`
                in our docs.

        Returns:
            The property. ``None`` will be returned if `key`
            is not present in the database or `path` leads to
            a non-existent property.

        Raises:
            TypeError: If the property is not a string.
        """
        result = self.connection.execute(
            "SELECT json_extract(properties,?), "  # noqa: S608
            "json_type(properties,?) "
            f"FROM {self._molecule_table} "
            "WHERE key=? LIMIT 1",
            (path, path, key),
        ).fetchone()
        if result is None:
            return None
        property_value, property_type = result
        if property_type is None:
            return None
        if property_type != "text":
            msg = f"{property_type} property is not a str: {property_value}"
            raise TypeError(msg)
        return property_value

    def set_str_property(
        self,
        key: str,
        path: str,
        property: str,  # noqa: A002
        *,
        commit: bool = True,
    ) -> None:
        """Set a string property of a molecule.

        Parameters:
            key:
                The key of the molecule.
            path:
                A path to the property of the molecule. Valid
                paths are described
                `here <https://www.sqlite.org/json1.html#path_arguments>`_.
                You can also view various code
                :ref:`examples<examples-valid-property-paths>`
                in our docs.
            property:
                The desired value of the property.
            commit:
                If ``True`` changes will be automatically
                commited to the database file.
        """
        self.set_property(key, path, property, commit=commit)

    def get_property(self, key: str, path: str) -> "Json":
        """Get the property of a molecule.

        .. note::

            If `path` does not lead to a property which exists,
            ``None`` will be returned. This means that the same
            value is returned for a missing value as well as an
            exisiting value set to ``None``. If you need to
            distinguish between missing and ``None`` values you
            can use a different value to represent missing data,
            for example the string ``"MISSING"``.

        Parameters:
            key:
                The key of the molecule.
            path:
                A path to the property of the molecule. Valid
                paths are described
                `here <https://www.sqlite.org/json1.html#path_arguments>`_.
                You can also view various code
                :ref:`examples<examples-valid-property-paths>`
                in our docs.

        Returns:
            The property. ``None`` will be returned if `key`
            is not present in the database or `path` leads to
            a non-existent property.
        """
        result = self.connection.execute(
            "SELECT json_extract(properties,?), "  # noqa: S608
            "json_type(properties,?) "
            f"FROM {self._molecule_table} "
            "WHERE key=? LIMIT 1",
            (path, path, key),
        ).fetchone()
        if result is None:
            return None
        property_value, property_type = result
        if property_type in {"object", "array"}:
            return json.loads(property_value)
        if property_type in {"true", "false"}:
            return bool(property_value)
        return property_value

    def set_property(
        self,
        key: str,
        path: str,
        property: float | str | bool | None,  # noqa: A002
        *,
        commit: bool = True,
    ) -> None:
        """Set the property of a molecule.

        Parameters:
            key:
                The key of the molecule.
            path:
                A path to the property of the molecule. Valid
                paths are described
                `here <https://www.sqlite.org/json1.html#path_arguments>`_.
                You can also view various code
                :ref:`examples<examples-valid-property-paths>`
                in our docs.
            property:
                The desired value of the property.
            commit:
                If ``True`` changes will be automatically
                commited to the database file.
        """
        match property:
            case None:
                value = "null"
            case bool():
                value = "true" if property else "false"
            case int():
                value = str(property)
            case float():
                value = str(property)
            case str():
                value = json.dumps(property)
            case _ as unreachable:
                typing.assert_never(unreachable)
        self.connection.execute(
            f"INSERT INTO {self._molecule_table} (key,properties)"
            f"VALUES (:key,json_set('{{}}',:path,json('{value}'))) "
            "ON CONFLICT(key) DO UPDATE "
            f"SET properties=json_set(properties,:path,json('{value}')) "
            "WHERE key=:key",
            {"key": key, "path": path, "property": property},
        )
        if commit:
            self.connection.commit()

    def remove_property(
        self, key: str, path: str, *, commit: bool = True
    ) -> None:
        """Remove a property from a molecule.

        Parameters:
            key:
                The key of the molecule.
            path:
                A path to the property of the molecule. Valid
                paths are described
                `here <https://www.sqlite.org/json1.html#path_arguments>`_.
                You can also view various code
                :ref:`examples<examples-valid-property-paths>`
                in our docs.
            commit:
                If ``True`` changes will be automatically
                commited to the database file.
        """
        self.connection.execute(
            f"UPDATE {self._molecule_table} "  # noqa: S608
            "SET properties=json_remove(properties,:path) "
            "WHERE key=:key",
            {"key": key, "path": path},
        )
        if commit:
            self.connection.commit()

    def update_properties(
        self,
        entries: PropertyEntry | collections.abc.Iterable[PropertyEntry],
        *,
        merge_properties: bool = True,
        commit: bool = True,
    ) -> None:
        """Update property entries in the database.

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
                f"UPDATE {self._molecule_table} "  # noqa: S608
                "SET properties=json_patch(properties,:properties) "
                "WHERE key=:key",
                map(_property_entry_to_sqlite, entries),
            )
        else:
            self.connection.executemany(
                f"UPDATE {self._molecule_table} "  # noqa: S608
                "SET properties=:properties "
                "WHERE key=:key",
                map(_property_entry_to_sqlite, entries),
            )
        if commit:
            self.connection.commit()


def _iter_props(
    prop_names: collections.abc.Sequence[str],
    props: collections.abc.Sequence[typing.Any],
) -> collections.abc.Iterator[tuple[str, typing.Any, str]]:
    for name, i in zip(prop_names, range(0, len(props), 2), strict=True):
        yield name, props[i], props[i + 1]
