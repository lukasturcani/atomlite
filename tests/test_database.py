import atomlite
import numpy as np
import pytest
import rdkit.Chem as rdkit


@pytest.mark.parametrize(
    ["molecules", "properties"],
    [
        [rdkit.MolFromSmiles("CCC"), {}],
    ],
)
def test_database_stores_molecular_data(
    database: atomlite.Database,
    molecules: rdkit.Mol | tuple[rdkit.Mol, ...],
    properties: dict,
) -> None:
    if not isinstance(molecules, tuple):
        entries: atomlite.Entry | tuple[
            atomlite.Entry, ...
        ] = atomlite.Entry.from_rdkit("1", molecules)
    else:
        entries = tuple(
            atomlite.Entry.from_rdkit(str(key), molecule)
            for key, molecule in enumerate(molecules)
        )

    database.add_molecules(entries)
    if isinstance(entries, atomlite.Entry):
        retrieved = {
            key: atomlite.to_rdkit(molecule)
            for key, molecule in database.get_molecules(entries.key)
        }
        molecules = (molecules,)
        entries = (entries,)
    else:
        retrieved = {
            key: atomlite.to_rdkit(molecule)
            for key, molecule in database.get_molecules(
                entry.key for entry in entries
            )
        }

    for entry, molecule in zip(entries, molecules, strict=True):
        actual = retrieved[entry.key]
        _assert_conformers_match(molecule, actual)
        _assert_atom_numbers_match(molecule, actual)
        _assert_properties_match(molecule, actual)


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


def _assert_properties_match(expected: rdkit.Mol, actual: rdkit.Mol) -> None:
    pass


@pytest.fixture
def database() -> atomlite.Database:
    return atomlite.Database(":memory:")
