import json
from dataclasses import dataclass

import atomlite
import numpy as np
import pytest
import rdkit.Chem.AllChem as rdkit


@dataclass(frozen=True, slots=True)
class SingleEntryCase:
    entry: atomlite.Entry
    molecule: rdkit.Mol


@dataclass(frozen=True, slots=True)
class MultipleEntryCase:
    entries: tuple[atomlite.Entry, ...]
    molecules: tuple[rdkit.Mol, ...]


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
    database.update_entries(entry2, merge_properties=False)
    entry = next(database.get_entries("first"))
    molecule = atomlite.json_to_rdkit(entry.molecule)
    assert molecule.GetNumAtoms() == 2
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
    database.update_entries(entry2)
    entry = next(database.get_entries("first"))
    molecule = atomlite.json_to_rdkit(entry.molecule)
    assert molecule.GetNumAtoms() == 2
    assert entry.properties == {"a": 12, "b": 32}


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
    assert len(retrieved) == 3
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


def _assert_conformers_match(expected: rdkit.Mol, actual: rdkit.Mol) -> None:
    for conformer1, conformer2 in zip(
        expected.GetConformers(), actual.GetConformers(), strict=True
    ):
        assert np.all(
            np.equal(conformer1.GetPositions(), conformer2.GetPositions())
        )


def _assert_atom_numbers_match(expected: rdkit.Mol, actual: rdkit.Mol) -> None:
    expected.UpdatePropertyCache()
    actual.UpdatePropertyCache()
    assert expected.GetNumAtoms() == actual.GetNumAtoms()
    assert expected.GetNumHeavyAtoms() == actual.GetNumHeavyAtoms()
    for atom1, atom2 in zip(
        expected.GetAtoms(), actual.GetAtoms(), strict=True
    ):
        assert atom1.GetTotalNumHs() == atom2.GetTotalNumHs()
        assert atom1.GetNumExplicitHs() == atom2.GetNumExplicitHs()
        assert atom1.GetNumImplicitHs() == atom2.GetNumImplicitHs()


def _assert_properties_match(
    expected: dict | None,
    actual: dict | None,
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
                rdkit.AddHs(rdkit.MolFromSmiles("CCC"))
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
                )
            )
        ),
        molecules=param["molecules"],
    )


@pytest.fixture
def database() -> atomlite.Database:
    return atomlite.Database(":memory:")
