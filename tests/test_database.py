import atomlite
import numpy as np
import pytest
import rdkit.Chem as rdkit


@pytest.mark.parametrize(
    "molecules",
    (atomlite.Entry("1", rdkit.MolFromSmiles("CCC")),),
)
def test_database_stores_molecular_data(
    database: atomlite.Database,
    molecules: atomlite.Entry | tuple[atomlite.Entry, ...],
) -> None:
    database.add_molecules(molecules)
    if isinstance(molecules, atomlite.Entry):
        retrieved = database.get_molecules(molecules.key)
        molecules = (molecules,)
    else:
        retrieved = database.get_molecules(entry.key for entry in molecules)

    for expected, actual in zip(molecules, retrieved, strict=True):
        _assert_conformers_match(expected.molecule, actual.molecule)
        _assert_atom_numbers_match(expected.molecule, actual.molecule)


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
    assert expected.GetNumImplicitHs() == actual.GetNumImplicitHs()
    assert expected.GetNumExplicitHs() == actual.GetNumExplicitHs()


@pytest.fixture
def database() -> atomlite.Database:
    return atomlite.Database(":memory:")
