"""Write the ChEMBL database to an AtomLite file."""  # noqa: INP001

import argparse
from pathlib import Path

import atomlite
import rdkit.Chem as rdkit  # noqa: N813


def main() -> None:
    """Run the example."""
    args = _parse_args()
    chembl = rdkit.SDMolSupplier(args.chembl)
    db = atomlite.Database(args.output)
    for i, mol in enumerate(chembl):
        db.add_entries(
            atomlite.Entry.from_rdkit(
                key=str(i),
                molecule=mol,
                properties=mol.GetPropsAsDict(),
            ),
            commit=False,
        )
    db.connection.commit()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "chembl",
        help="Path to the ChEMBL sdf database file.",
        type=Path,
    )
    parser.add_argument(
        "output",
        help="Path to the output atomlite file.",
        type=Path,
    )
    return parser.parse_args()


if __name__ == "__main__":
    main()
