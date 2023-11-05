import atomlite
import rdkit.Chem as rdkit  # noqa: N813


def test_aromatic_json_serde() -> None:
    molecule = rdkit.MolFromSmiles("c1ccccc1")
    serde_result = atomlite.json_to_rdkit(atomlite.json_from_rdkit(molecule))
    assert rdkit.MolToSmiles(serde_result) == "c1ccccc1"


def test_json_serde() -> None:
    molecule = rdkit.MolFromSmiles("C=CC#CCC")
    serde_result = atomlite.json_to_rdkit(atomlite.json_from_rdkit(molecule))
    assert rdkit.MolToSmiles(serde_result) == "C=CC#CCC"


def test_charged_json_serde() -> None:
    molecule = rdkit.MolFromSmiles("O=C[O-]")
    serde_result = atomlite.json_to_rdkit(atomlite.json_from_rdkit(molecule))
    assert rdkit.MolToSmiles(serde_result) == "O=C[O-]"


def test_dative_json_serde() -> None:
    molecule = rdkit.MolFromSmiles("Cl->[Fe]")
    serde_result = atomlite.json_to_rdkit(atomlite.json_from_rdkit(molecule))
    assert rdkit.MolToSmiles(serde_result) == "Cl->[Fe]"
