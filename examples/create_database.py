# noqa: INP001
"""Create a database from an SDF file.

This script creates a database from an SDF file. I like to run it
with ChEBI, which you can download from
https://ftp.ebi.ac.uk/pub/databases/chebi/SDF/ChEBI_complete.sdf.gz.

The output atomlite database will have the molecules from the input
SDF file along with all the properties that are stored in the sdf file.
"""
import argparse
from collections.abc import Iterator
from pathlib import Path

import atomlite
import rdkit.Chem as rdkit  # noqa: N813


def main() -> None:
    """Do the thing."""
    args = _parse_args()
    database = atomlite.Database(args.output)
    database.add_entries(_get_entries(args.input))


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    return parser.parse_args()


def _get_entries(file: Path) -> Iterator[atomlite.Entry]:
    suppl = rdkit.SDMolSupplier(str(file))
    for i, molecule in enumerate(suppl):
        if molecule is not None:
            try:
                yield atomlite.Entry.from_rdkit(
                    key=f"{i}",
                    molecule=molecule,
                    properties=molecule.GetPropsAsDict(includePrivate=True),
                )
            except atomlite.SerializationError:
                continue


if __name__ == "__main__":
    main()
