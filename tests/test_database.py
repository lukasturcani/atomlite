import json
from dataclasses import dataclass

import atomlite
import numpy as np
import pytest
import rdkit.Chem as rdkit


@dataclass(frozen=True, slots=True)
class SingleEntryCase:
    entry: atomlite.Entry
    molecule: rdkit.Mol


@dataclass(frozen=True, slots=True)
class MultipleEntryCase:
    entries: tuple[atomlite.Entry, ...]
    molecules: tuple[rdkit.Mol, ...]


def test_database_stores_molecular_data_single_entry(
    database: atomlite.Database,
    single_entry_case: SingleEntryCase,
) -> None:
    database.add_molecules(single_entry_case.entry)
    retrieved = {
        key: (atomlite.to_rdkit(molecule), molecule["properties"])
        for key, molecule in database.get_molecules(
            single_entry_case.entry.key
        )
    }
    actual, props = retrieved[single_entry_case.entry.key]
    _assert_conformers_match(single_entry_case.molecule, actual)
    _assert_atom_numbers_match(single_entry_case.molecule, actual)
    _assert_properties_match(
        single_entry_case.entry.molecule["properties"],
        props,
    )


def test_database_stores_molecular_data_multiple_entries(
    database: atomlite.Database,
    multiple_entry_case: MultipleEntryCase,
) -> None:
    database.add_molecules(multiple_entry_case.entries)
    retrieved = {
        key: (atomlite.to_rdkit(molecule), molecule["properties"])
        for key, molecule in database.get_molecules(
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
        _assert_properties_match(entry.molecule["properties"], props)


def _assert_conformers_match(expected: rdkit.Mol, actual: rdkit.Mol) -> None:
    for conformer1, conformer2 in zip(
        expected.GetConformers(), actual.GetConformers(), strict=True
    ):
        assert np.all(
            np.equal(conformer1.GetPositions(), conformer2.GetPositions())
        )


def _assert_atom_numbers_match(expected: rdkit.Mol, actual: rdkit.Mol) -> None:
    assert expected.GetNumAtoms() == actual.GetNumAtoms()
    assert expected.GetNumHeavyAtoms() == actual.GetNumHeavyAtoms()
    expected.UpdatePropertyCache()
    actual.UpdatePropertyCache()
    for atom1, atom2 in zip(
        expected.GetAtoms(), actual.GetAtoms(), strict=True
    ):
        assert atom1.GetNumImplicitHs() == atom2.GetNumImplicitHs()
        assert atom1.GetNumExplicitHs() == atom2.GetNumExplicitHs()


def _assert_properties_match(expected: dict, actual: dict) -> None:
    assert json.dumps(expected) == json.dumps(actual)


@pytest.fixture(
    params=(
        (
            rdkit.MolFromSmiles("CCC"),
            {"a": {"b": [1, 2, 3]}},
        ),
    ),
)
def single_entry_case(request: pytest.FixtureRequest) -> SingleEntryCase:
    molecule, properties = request.param
    return SingleEntryCase(
        entry=atomlite.Entry.from_rdkit("1", molecule, properties),
        molecule=molecule,
    )


@pytest.fixture(
    params=(
        (
            (rdkit.MolFromSmiles("CCC"),),
            ({"a": {"b": [1, 2, 3]}},),
        ),
        (
            (
                rdkit.MolFromSmiles("CCC"),
                rdkit.MolFromSmiles("CNC"),
                rdkit.AddHs(rdkit.MolFromSmiles("CNC")),
            ),
            (
                {"a": {"b": [1, 2, 3]}},
                {"b": 231},
                {"c": 32231},
            ),
        ),
    ),
)
def multiple_entry_case(request: pytest.FixtureRequest) -> MultipleEntryCase:
    molecules, properties = request.param
    return MultipleEntryCase(
        entries=tuple(
            atomlite.Entry.from_rdkit(str(key), molecule, props)
            for key, (molecule, props) in enumerate(
                zip(
                    molecules,
                    properties,
                    strict=True,
                )
            )
        ),
        molecules=molecules,
    )


@pytest.fixture
def database() -> atomlite.Database:
    return atomlite.Database(":memory:")
