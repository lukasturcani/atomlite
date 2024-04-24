"""Write a database from an SDF file."""  # noqa: INP001

import argparse
from pathlib import Path

import atomlite
import rdkit.Chem as rdkit  # noqa: N813


def main() -> None:
    """Run the example."""
    args = _parse_args()
    sdf = rdkit.SDMolSupplier(args.sdf)
    db = atomlite.Database(args.output)
    for i, mol in enumerate(sdf):
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
        "sdf",
        help="Path to the sdf file.",
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
