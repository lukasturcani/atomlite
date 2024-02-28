import json
from collections import defaultdict
from dataclasses import dataclass

import atomlite
import numpy as np
import polars as pl
import polars.testing as pl_testing
import pytest
import rdkit.Chem.AllChem as rdkit  # noqa: N813


@dataclass(frozen=True, slots=True)
class SingleEntryCase:
    entry: atomlite.Entry
    molecule: rdkit.Mol


@dataclass(frozen=True, slots=True)
class MultipleEntryCase:
    entries: tuple[atomlite.Entry, ...]
    molecules: tuple[rdkit.Mol, ...]


def test_defaultdict_entry_works(database: atomlite.Database) -> None:
    d1: dict[str, atomlite.Json] = defaultdict(list)
    d1["hello"] = [1, 2, 3]
    entry = atomlite.Entry.from_rdkit("first", rdkit.MolFromSmiles("C"), d1)
    database.add_entries(entry)
    retrieved = database.get_entry("first")
    assert retrieved is not None
    _assert_properties_match(entry.properties, retrieved.properties)


def test_defaultdict_property_entry_works(database: atomlite.Database) -> None:
    d1: dict[str, atomlite.Json] = defaultdict(list)
    d1["hello"] = [1, 2, 3]
    entry = atomlite.Entry.from_rdkit("first", rdkit.MolFromSmiles("C"))
    property_entry = atomlite.PropertyEntry("first", d1)
    database.add_entries(entry)
    database.update_properties(property_entry)
    retrieved = database.get_entry("first")
    assert retrieved is not None
    _assert_properties_match(property_entry.properties, retrieved.properties)


def test_bool_property_methods(database: atomlite.Database) -> None:
    entry = atomlite.Entry.from_rdkit(
        "first", rdkit.MolFromSmiles("C"), {"a": True, "b": 12}
    )
    database.add_entries(entry)
    prop = database.get_bool_property("missing", "$.a")
    assert prop is None
    prop = database.get_bool_property("first", "$.missing")
    assert prop is None
    prop = database.get_bool_property("first", "$.a")
    assert prop is True
    database.set_bool_property("first", "$.a", property=False)
    prop = database.get_bool_property("first", "$.a")
    assert prop is False
    database.set_bool_property("first", "$.a", property=True)
    prop = database.get_bool_property("first", "$.a")
    assert prop is True

    with pytest.raises(TypeError):
        database.get_bool_property("first", "$.b")


def test_int_property_methods(database: atomlite.Database) -> None:
    entry = atomlite.Entry.from_rdkit(
        "first", rdkit.MolFromSmiles("C"), {"a": True, "b": 12}
    )
    database.add_entries(entry)
    prop = database.get_int_property("missing", "$.a")
    assert prop is None
    prop = database.get_int_property("first", "$.missing")
    assert prop is None
    prop = database.get_int_property("first", "$.b")
    assert prop == 12  # noqa: PLR2004
    database.set_int_property("first", "$.b", 9)
    prop = database.get_int_property("first", "$.b")
    assert prop == 9  # noqa: PLR2004

    with pytest.raises(TypeError):
        database.get_int_property("first", "$.a")


def test_float_property_methods(database: atomlite.Database) -> None:
    entry = atomlite.Entry.from_rdkit(
        "first", rdkit.MolFromSmiles("C"), {"a": True, "b": 12.5}
    )
    database.add_entries(entry)
    prop = database.get_float_property("missing", "$.a")
    assert prop is None
    prop = database.get_float_property("first", "$.missing")
    assert prop is None
    prop = database.get_float_property("first", "$.b")
    assert prop == 12.5  # noqa: PLR2004
    database.set_float_property("first", "$.b", 9.7)
    prop = database.get_float_property("first", "$.b")
    assert prop == 9.7  # noqa: PLR2004

    with pytest.raises(TypeError):
        database.get_float_property("first", "$.a")


def test_str_property_methods(database: atomlite.Database) -> None:
    entry = atomlite.Entry.from_rdkit(
        "first", rdkit.MolFromSmiles("C"), {"a": True, "b": "hello"}
    )
    database.add_entries(entry)
    prop = database.get_str_property("missing", "$.a")
    assert prop is None
    prop = database.get_str_property("first", "$.missing")
    assert prop is None
    prop = database.get_str_property("first", "$.b")
    assert prop == "hello"
    database.set_str_property("first", "$.b", "bye")
    prop = database.get_str_property("first", "$.b")
    assert prop == "bye"

    with pytest.raises(TypeError):
        database.get_str_property("first", "$.a")


def test_remove_entries(database: atomlite.Database) -> None:
    entry1 = atomlite.Entry.from_rdkit("first", rdkit.MolFromSmiles("C"))
    entry2 = atomlite.Entry.from_rdkit("second", rdkit.MolFromSmiles("C"))
    database.add_entries([entry1, entry2])
    assert database.has_entry("first")
    database.remove_entries("first")
    assert not database.has_entry("first")


def test_remove_property(database: atomlite.Database) -> None:
    entry = atomlite.Entry.from_rdkit(
        "first", rdkit.MolFromSmiles("C"), {"a": {"b": 12}}
    )
    database.add_entries(entry)
    assert database.get_property("first", "$.a.b") == 12  # noqa: PLR2004
    database.remove_property("first", "$.a.b")
    assert database.get_property("first", "$.a.b") is None


def test_get_property_entry(database: atomlite.Database) -> None:
    database.set_property("first", "$.a.b", 12)
    prop_entry = database.get_property_entry("first")
    assert prop_entry is not None
    assert prop_entry.key == "first"
    assert prop_entry.properties == {"a": {"b": 12}}
    prop_entry = database.get_property_entry("second")
    assert prop_entry is None


def test_get_property_entries_returns_all_entries(
    database: atomlite.Database,
) -> None:
    database.set_property("first", "$.a.b", 12)
    database.set_property("second", "$.a.b", 12)
    prop_entries = list(database.get_property_entries())
    assert len(prop_entries) == 2  # noqa: PLR2004
    assert prop_entries[0].key == "first"
    assert prop_entries[0].properties == {"a": {"b": 12}}
    assert prop_entries[1].key == "second"
    assert prop_entries[1].properties == {"a": {"b": 12}}


def test_get_property_entries_returns_entries_of_keys(
    database: atomlite.Database,
) -> None:
    database.set_property("first", "$.a.b", 12)
    database.set_property("second", "$.a.b", 12)
    (prop_entry,) = list(database.get_property_entries("first"))
    assert prop_entry.key == "first"
    assert prop_entry.properties == {"a": {"b": 12}}


def test_num_entries(database: atomlite.Database) -> None:
    assert database.num_entries() == 0
    entry = atomlite.Entry.from_rdkit("first", rdkit.MolFromSmiles("C"))
    database.add_entries(entry)
    assert database.num_entries() == 1
    entry = atomlite.Entry.from_rdkit("second", rdkit.MolFromSmiles("CC"))
    database.add_entries(entry)
    assert database.num_entries() == 2  # noqa: PLR2004
    entry = atomlite.Entry.from_rdkit("third", rdkit.MolFromSmiles("CCC"))
    database.add_entries(entry, commit=False)
    assert database.num_entries() == 3  # noqa: PLR2004
    database.set_property("fourth", "$.a", 12)
    assert database.num_entries() == 3  # noqa: PLR2004


def test_property_num_entries(database: atomlite.Database) -> None:
    assert database.num_property_entries() == 0
    entry = atomlite.Entry.from_rdkit("first", rdkit.MolFromSmiles("C"))
    database.add_entries(entry)
    assert database.num_property_entries() == 1
    entry = atomlite.Entry.from_rdkit("second", rdkit.MolFromSmiles("CC"))
    database.add_entries(entry)
    assert database.num_property_entries() == 2  # noqa: PLR2004
    entry = atomlite.Entry.from_rdkit("third", rdkit.MolFromSmiles("CCC"))
    database.add_entries(entry, commit=False)
    assert database.num_property_entries() == 3  # noqa: PLR2004
    database.set_property("fourth", "$.a", 12)
    assert database.num_property_entries() == 4  # noqa: PLR2004


def test_has_entry(database: atomlite.Database) -> None:
    entry = atomlite.Entry.from_rdkit("first", rdkit.MolFromSmiles("C"))
    database.add_entries(entry)
    database.set_property("second", "$.a", 12)
    assert database.has_entry("first")
    assert not database.has_entry("second")
    assert not database.has_entry("third")


def test_has_property_entry(database: atomlite.Database) -> None:
    entry = atomlite.Entry.from_rdkit("first", rdkit.MolFromSmiles("C"))
    database.add_entries(entry)
    database.set_property("second", "$.a", 12)
    assert database.has_property_entry("first")
    assert database.has_property_entry("second")
    assert not database.has_property_entry("third")


def test_set_property(database: atomlite.Database) -> None:
    entry = atomlite.Entry.from_rdkit(
        key="first",
        molecule=rdkit.MolFromSmiles("C"),
        properties={
            "a": {
                "b": 12,
            },
        },
    )
    database.add_entries(entry)
    database.set_property("first", "$.a.c", 12)
    assert database.get_property("first", "$.a.c") == 12  # noqa: PLR2004
    database.set_property("second", "$.d.e", "hi")
    assert database.get_property("second", "$.d.e") == "hi"
    (entry,) = database.get_entries()
    assert entry.key == "first"
    database.set_property("first", "$.a.boolean", property=False)
    assert database.get_property("first", "$.a.boolean") is False
    database.set_property("first", "$.a.none", None)
    assert database.get_property("first", "$.a.none") is None
    database.set_property("first", "$.a.float", 13.5)
    assert database.get_property("first", "$.a.float") == 13.5  # noqa: PLR2004


def test_get_missing_property(database: atomlite.Database) -> None:
    entry = atomlite.Entry.from_rdkit(
        key="first",
        molecule=rdkit.MolFromSmiles("C"),
        properties={
            "a": {
                "b": 12,
            },
        },
    )
    database.add_entries(entry)
    assert database.get_property("first", "$.a.not_here") is None


def test_get_property_from_missing_molecule(
    database: atomlite.Database,
) -> None:
    assert database.get_property("first", "$.a.a") is None


def test_get_property(database: atomlite.Database) -> None:
    entry = atomlite.Entry.from_rdkit(
        key="first",
        molecule=rdkit.MolFromSmiles("C"),
        properties={
            "a": {
                "b": 12,
                "c": [1, 2, 3],
                "d": "[4, 5, 6]",
                "e": "hi",
                "f": None,
                "g": {"a": 12, "b": 24},
                "h": True,
                "i": False,
                "j": 12.2,
            },
        },
    )
    database.add_entries(entry)
    assert database.get_property("first", "$.a.b") == 12  # noqa: PLR2004
    assert database.get_property("first", "$.a.c") == [1, 2, 3]
    assert database.get_property("first", "$.a.d") == "[4, 5, 6]"
    assert database.get_property("first", "$.a.e") == "hi"
    assert database.get_property("first", "$.a.f") is None
    assert database.get_property("first", "$.a.g") == {"a": 12, "b": 24}
    assert database.get_property("first", "$.a.h") is True
    assert database.get_property("first", "$.a.i") is False
    assert database.get_property("first", "$.a.j") == 12.2  # noqa: PLR2004


def test_entry_is_replaced_on_update(database: atomlite.Database) -> None:
    entry1 = atomlite.Entry.from_rdkit(
        key="first",
        molecule=rdkit.MolFromSmiles("C"),
        properties={"a": 12},
    )
    database.add_entries(entry1)
    entry2 = atomlite.Entry.from_rdkit(
        key="first",
        molecule=rdkit.MolFromSmiles("CC"),
        properties={"b": 32},
    )
    database.update_entries(entry2, merge_properties=False, upsert=False)
    entry = next(database.get_entries("first"))
    molecule = atomlite.json_to_rdkit(entry.molecule)
    assert molecule.GetNumAtoms() == 2  # noqa: PLR2004
    assert entry.properties == {"b": 32}


def test_properties_get_merged_on_entry_update(
    database: atomlite.Database,
) -> None:
    entry1 = atomlite.Entry.from_rdkit(
        key="first",
        molecule=rdkit.MolFromSmiles("C"),
        properties={"a": 12, "b": 10},
    )
    database.add_entries(entry1)
    entry2 = atomlite.Entry.from_rdkit(
        key="first",
        molecule=rdkit.MolFromSmiles("CC"),
        properties={"b": 32},
    )
    database.update_entries(entry2, upsert=False)
    entry = next(database.get_entries("first"))
    molecule = atomlite.json_to_rdkit(entry.molecule)
    assert molecule.GetNumAtoms() == 2  # noqa: PLR2004
    assert entry.properties == {"a": 12, "b": 32}


def test_upsert(
    database: atomlite.Database,
) -> None:
    entry1 = atomlite.Entry.from_rdkit(
        key="first",
        molecule=rdkit.MolFromSmiles("C"),
        properties={"a": 12, "b": 10},
    )
    database.update_entries(entry1, upsert=False)
    assert len(list(database.get_entries("first"))) == 0
    database.update_entries(entry1, upsert=True)
    (result1,) = list(database.get_entries("first"))
    molecule1 = atomlite.json_to_rdkit(result1.molecule)
    assert molecule1.GetNumAtoms() == 1
    assert result1.properties == {"a": 12, "b": 10}

    entry2 = atomlite.Entry.from_rdkit(
        key="first",
        molecule=rdkit.MolFromSmiles("CC"),
        properties={"b": 32},
    )
    database.update_entries(entry2, merge_properties=True, upsert=True)
    (result2,) = list(database.get_entries("first"))
    molecule2 = atomlite.json_to_rdkit(result2.molecule)
    assert molecule2.GetNumAtoms() == 2  # noqa: PLR2004
    assert result2.properties == {"a": 12, "b": 32}

    entry3 = atomlite.Entry.from_rdkit(
        key="first",
        molecule=rdkit.MolFromSmiles("CCC"),
        properties={"b": 64},
    )
    database.update_entries(entry3, merge_properties=False, upsert=True)
    (result3,) = list(database.get_entries("first"))
    molecule3 = atomlite.json_to_rdkit(result3.molecule)
    assert molecule3.GetNumAtoms() == 3  # noqa: PLR2004
    assert result3.properties == {"b": 64}


def test_properties_get_merged_on_property_update(
    database: atomlite.Database,
) -> None:
    entry1 = atomlite.Entry.from_rdkit(
        key="first",
        molecule=rdkit.MolFromSmiles("C"),
        properties={"a": 12, "b": 10},
    )
    database.add_entries(entry1)
    entry2 = atomlite.PropertyEntry(
        key="first",
        properties={"b": 32},
    )
    database.update_properties(entry2)
    entry = next(database.get_entries("first"))
    molecule = atomlite.json_to_rdkit(entry.molecule)
    assert molecule.GetNumAtoms() == 1
    assert entry.properties == {"a": 12, "b": 32}


def test_properties_get_replaced_on_property_update(
    database: atomlite.Database,
) -> None:
    entry1 = atomlite.Entry.from_rdkit(
        key="first",
        molecule=rdkit.MolFromSmiles("C"),
        properties={"a": 12, "b": 10},
    )
    database.add_entries(entry1)
    entry2 = atomlite.PropertyEntry(
        key="first",
        properties={"b": 32},
    )
    database.update_properties(entry2, merge_properties=False)
    entry = next(database.get_entries("first"))
    molecule = atomlite.json_to_rdkit(entry.molecule)
    assert molecule.GetNumAtoms() == 1
    assert entry.properties == {"b": 32}


def test_get_entries_returns_all_entries(
    database: atomlite.Database,
) -> None:
    entry1 = atomlite.Entry.from_rdkit("first", rdkit.MolFromSmiles("C"))
    entry2 = atomlite.Entry.from_rdkit("second", rdkit.MolFromSmiles("C"))
    entry3 = atomlite.Entry.from_rdkit("third", rdkit.MolFromSmiles("C"))
    database.add_entries([entry1, entry2, entry3])

    retrieved = [entry.key for entry in database.get_entries()]
    assert len(retrieved) == 3  # noqa: PLR2004
    assert set(retrieved) == {"first", "second", "third"}


def test_database_stores_molecular_data_single_entry(
    database: atomlite.Database,
    single_entry_case: SingleEntryCase,
) -> None:
    database.add_entries(single_entry_case.entry)
    retrieved = {
        entry.key: (atomlite.json_to_rdkit(entry.molecule), entry.properties)
        for entry in database.get_entries(single_entry_case.entry.key)
    }
    actual, props = retrieved[single_entry_case.entry.key]
    _assert_conformers_match(single_entry_case.molecule, actual)
    _assert_atom_numbers_match(single_entry_case.molecule, actual)
    _assert_properties_match(single_entry_case.entry.properties, props)


def test_database_stores_molecular_data_multiple_entries(
    database: atomlite.Database,
    multiple_entry_case: MultipleEntryCase,
) -> None:
    database.add_entries(multiple_entry_case.entries)
    retrieved = {
        entry.key: (atomlite.json_to_rdkit(entry.molecule), entry.properties)
        for entry in database.get_entries(
            entry.key for entry in multiple_entry_case.entries
        )
    }

    for entry, molecule in zip(
        multiple_entry_case.entries,
        multiple_entry_case.molecules,
        strict=True,
    ):
        actual, props = retrieved[entry.key]
        _assert_conformers_match(molecule, actual)
        _assert_atom_numbers_match(molecule, actual)
        _assert_properties_match(entry.properties, props)
        assert rdkit.MolToSmiles(molecule) == rdkit.MolToSmiles(actual)


def test_get_entry(
    database: atomlite.Database,
    single_entry_case: SingleEntryCase,
) -> None:
    database.add_entries(single_entry_case.entry)
    retrieved = database.get_entry(single_entry_case.entry.key)
    assert retrieved is not None
    retrieved_molecule = atomlite.json_to_rdkit(retrieved.molecule)
    assert retrieved.key == single_entry_case.entry.key
    _assert_conformers_match(single_entry_case.molecule, retrieved_molecule)
    _assert_atom_numbers_match(single_entry_case.molecule, retrieved_molecule)
    _assert_properties_match(
        single_entry_case.entry.properties, retrieved.properties
    )


def test_get_entry_returns_none_for_missing_key(
    database: atomlite.Database,
) -> None:
    retrieved = database.get_entry("first")
    assert retrieved is None


def _assert_conformers_match(expected: rdkit.Mol, actual: rdkit.Mol) -> None:
    for conformer1, conformer2 in zip(
        expected.GetConformers(),
        actual.GetConformers(),
        strict=True,
    ):
        assert np.all(
            np.equal(conformer1.GetPositions(), conformer2.GetPositions()),
        )


def test_get_property_df_and() -> None:
    db = atomlite.Database(":memory:")
    db.add_entries(
        [
            atomlite.Entry.from_rdkit(
                "first",
                rdkit.MolFromSmiles("C"),
                {"a": 1, "b": 10.0},
            ),
            atomlite.Entry.from_rdkit(
                "second",
                rdkit.MolFromSmiles("CC"),
                {"a": 2, "b": 20.0, "c": "hi second"},
            ),
            atomlite.Entry.from_rdkit(
                "third",
                rdkit.MolFromSmiles("CCC"),
                {"a": 3, "b": 30.0, "c": "hi third", "d": [1, 2, 3]},
            ),
            atomlite.Entry.from_rdkit(
                "fourth",
                rdkit.MolFromSmiles("CCCC"),
                {"a": 4, "b": 40.0, "e": {"a": 12, "b": 24}},
            ),
            atomlite.Entry.from_rdkit(
                "five",
                rdkit.MolFromSmiles("CCCC"),
                {"a": 4, "b": 40.0, "f": True},
            ),
            atomlite.Entry.from_rdkit(
                "six",
                rdkit.MolFromSmiles("CCCC"),
                {"a": 4, "b": 40.0, "f": False},
            ),
        ]
    )
    pl_testing.assert_frame_equal(
        db.get_property_df(["$.a", "$.b"]),
        pl.DataFrame(
            {
                "key": ["first", "second", "third", "fourth", "five", "six"],
                "$.a": [1, 2, 3, 4, 4, 4],
                "$.b": [10.0, 20.0, 30.0, 40.0, 40.0, 40.0],
            }
        ),
    )
    pl_testing.assert_frame_equal(
        db.get_property_df(["$.a", "$.b", "$.c"]),
        pl.DataFrame(
            {
                "key": ["second", "third"],
                "$.a": [2, 3],
                "$.b": [20.0, 30.0],
                "$.c": ["hi second", "hi third"],
            }
        ),
    )
    pl_testing.assert_frame_equal(
        db.get_property_df(["$.a", "$.b", "$.e"]),
        pl.DataFrame(
            {
                "key": ["fourth"],
                "$.a": [4],
                "$.b": [40.0],
                "$.e": [{"a": 12, "b": 24}],
            }
        ),
    )
    pl_testing.assert_frame_equal(
        db.get_property_df(["$.a", "$.b", "$.d"]),
        pl.DataFrame(
            {
                "key": ["third"],
                "$.a": [3],
                "$.b": [30.0],
                "$.d": [[1, 2, 3]],
            }
        ),
    )
    pl_testing.assert_frame_equal(
        db.get_property_df(["$.a", "$.b", "$.f"]),
        pl.DataFrame(
            {
                "key": ["five", "six"],
                "$.a": [4, 4],
                "$.b": [40.0, 40.0],
                "$.f": [True, False],
            }
        ),
    )


def test_get_property_df_or() -> None:
    db = atomlite.Database(":memory:")
    db.add_entries(
        [
            atomlite.Entry.from_rdkit(
                "first",
                rdkit.MolFromSmiles("C"),
                {"a": 1, "b": 10.0},
            ),
            atomlite.Entry.from_rdkit(
                "second",
                rdkit.MolFromSmiles("CC"),
                {"a": 2, "b": 20.0, "c": "hi second"},
            ),
            atomlite.Entry.from_rdkit(
                "third",
                rdkit.MolFromSmiles("CCC"),
                {"a": 3, "b": 30.0, "c": "hi third"},
            ),
        ]
    )
    pl_testing.assert_frame_equal(
        db.get_property_df(["$.a", "$.b"], allow_missing=True),
        pl.DataFrame(
            {
                "key": ["first", "second", "third"],
                "$.a": [1, 2, 3],
                "$.b": [10.0, 20.0, 30.0],
            }
        ),
    )
    pl_testing.assert_frame_equal(
        db.get_property_df(["$.a", "$.b", "$.c"], allow_missing=True),
        pl.DataFrame(
            {
                "key": ["first", "second", "third"],
                "$.a": [1, 2, 3],
                "$.b": [10.0, 20.0, 30.0],
                "$.c": [None, "hi second", "hi third"],
            }
        ),
    )


def _assert_atom_numbers_match(expected: rdkit.Mol, actual: rdkit.Mol) -> None:
    expected.UpdatePropertyCache()
    actual.UpdatePropertyCache()
    assert expected.GetNumAtoms() == actual.GetNumAtoms()
    assert expected.GetNumHeavyAtoms() == actual.GetNumHeavyAtoms()
    for atom1, atom2 in zip(
        expected.GetAtoms(),
        actual.GetAtoms(),
        strict=True,
    ):
        assert atom1.GetTotalNumHs() == atom2.GetTotalNumHs()
        assert atom1.GetNumExplicitHs() == atom2.GetNumExplicitHs()
        assert atom1.GetNumImplicitHs() == atom2.GetNumImplicitHs()


def _assert_properties_match(
    expected: dict[str, atomlite.Json] | None,
    actual: dict[str, atomlite.Json] | None,
) -> None:
    assert json.dumps(expected) == json.dumps(actual)


def _embed_molecule(molecule: rdkit.Mol) -> rdkit.Mol:
    rdkit.EmbedMultipleConfs(molecule, 10, rdkit.ETKDGv3())
    return molecule


@pytest.fixture(
    params=(
        {
            "molecule": rdkit.MolFromSmiles("CCC"),
            "properties": {"a": {"b": [1, 2, 3]}},
        },
        {
            "molecule": _embed_molecule(rdkit.MolFromSmiles("CCC")),
            "properties": {"a": {"b": [1, 2, 3]}},
        },
        {
            "molecule": rdkit.AddHs(rdkit.MolFromSmiles("CCC")),
            "properties": {"a": {"b": [1, 2, 3]}},
        },
        {
            "molecule": _embed_molecule(
                rdkit.AddHs(rdkit.MolFromSmiles("CCC")),
            ),
            "properties": {"a": {"b": [1, 2, 3]}},
        },
    ),
)
def single_entry_case(request: pytest.FixtureRequest) -> SingleEntryCase:
    param = request.param
    return SingleEntryCase(
        entry=atomlite.Entry.from_rdkit(
            key="1",
            molecule=param["molecule"],
            properties=param["properties"],
        ),
        molecule=param["molecule"],
    )


@pytest.fixture(
    params=(
        {
            "molecules": (rdkit.MolFromSmiles("CCC"),),
            "properties": ({"a": {"b": [1, 2, 3]}},),
        },
        {
            "molecules": (
                rdkit.MolFromSmiles("CCC"),
                rdkit.MolFromSmiles("CNC"),
                rdkit.AddHs(rdkit.MolFromSmiles("CNC")),
            ),
            "properties": (
                {"a": {"b": [1, 2, 3]}},
                {"b": 231},
                {"c": 32231},
            ),
        },
    ),
)
def multiple_entry_case(request: pytest.FixtureRequest) -> MultipleEntryCase:
    param = request.param
    return MultipleEntryCase(
        entries=tuple(
            atomlite.Entry.from_rdkit(str(key), molecule, props)
            for key, (molecule, props) in enumerate(
                zip(
                    param["molecules"],
                    param["properties"],
                    strict=True,
                ),
            )
        ),
        molecules=param["molecules"],
    )


@pytest.fixture()
def database() -> atomlite.Database:
    return atomlite.Database(":memory:")
