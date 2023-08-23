import atomlite
import rdkit.Chem as rdkit


def test_json_serde() -> None:
    molecule = rdkit.MolFromSmiles("c1ccccc1")
    serde_result = atomlite.json_to_rdkit(atomlite.json_from_rdkit(molecule))
    assert rdkit.MolToSmiles(serde_result) == "c1ccccc1"
