import argparse
import logging
import pathlib

import rdkit.Chem as rdkit  # noqa: N813

from atomlite._internal.database import Database
from atomlite._internal.json import json_to_rdkit

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    dump = subparsers.add_parser(
        "dump",
        help="write a molecule from a database to a file (only .mol for now)",
    )
    dump.add_argument(
        "database_path",
        type=pathlib.Path,
        help="path to atomlite database",
    )
    dump.add_argument("entry_key", help="entry key of molecule")
    dump.add_argument(
        "dump_path",
        type=pathlib.Path,
        help="path to file",
    )

    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    if args.command == "dump":
        if args.dump_path.suffix not in (".mol",):
            msg = "only .mol files are supported"
            raise RuntimeError(msg)

        db = Database(args.database_path)
        rdkit.MolToMolFile(
            mol=json_to_rdkit(db.get_entry(args.entry_key).molecule),
            filename=args.dump_path,
            forceV3000=True,
        )
        logger.info("dumped %s to %s", args.entry_key, args.dump_path)


if __name__ == "__main__":
    main()
