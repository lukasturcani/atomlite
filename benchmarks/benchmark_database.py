from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Any

import atomlite


def benchmark_writing_molecules(tmp_path: Path, benchmark: Any) -> None:
    db = atomlite.Database(tmp_path / "test.db")
    benchmark(add_entries, db, create_entries(100_000))


def add_entries(
    database: atomlite.Database,
    entries: Iterable[atomlite.Entry],
) -> None:
    database.add_entries(entries)


def create_entries(num: int) -> Iterator[atomlite.Entry]:
    for i in range(num):
        yield atomlite.Entry(
            key=f"molecule_{i}",
            molecule={
                "atomic_numbers": list(range((i % 200) + 5)),
                "atom_charges": list(range((i % 200) + 5)),
                "bonds": {
                    "atom1": list(range((i % 200) + 5)),
                    "atom2": list(range((i % 200) + 6)),
                    "order": [i % 2 for _ in range((i % 200) + 5)],
                },
                "dative_bonds": {
                    "atom1": list(range((i % 200) + 3)),
                    "atom2": list(range((i % 200) + 4)),
                    "order": [i % 2 for _ in range((i % 200) + 3)],
                },
                "aromatic_bonds": {
                    "atom1": list(range((i % 200) + 7)),
                    "atom2": list(range((i % 200) + 8)),
                },
                "conformers": [
                    [[j, 2 * j, 3 * j] for j in range((i % 20) + 5)]
                    for _ in range(i % 20)
                ],
            },
            properties={
                "a": i,
                "b": i * 2,
                "c": False,
                "d": {"eaowjefoajfeoa": i, "f": i * 2},
                "g": [[i, i * 2, i * 3] for _ in range(10)],
                "haojfoieajf": None,
            },
        )
