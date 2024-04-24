"""Read all the molecules in a database."""  # noqa: INP001

import argparse
from pathlib import Path

import atomlite


def main() -> None:
    """Run the example."""
    args = _parse_args()
    db = atomlite.Database(args.database)
    for entry in db.get_entries():
        molecule = atomlite.json_to_rdkit(entry.molecule)  # noqa: F841
        # do something with molecule


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "database",
        help="Path to the atomlite file.",
        type=Path,
    )
    return parser.parse_args()


if __name__ == "__main__":
    main()
