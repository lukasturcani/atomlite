"""A SQLite chemical database."""

from atomlite._internal.database import (
    Database,
    Entry,
    PropertyEntry,
)
from atomlite._internal.json import (
    AromaticBonds,
    Bonds,
    Json,
    Molecule,
    json_from_rdkit,
    json_to_rdkit,
)

Json = Json  # noqa: PLW0127 - allow self assignment so docs work
"""A JSON value."""


__all__ = [
    "Bonds",
    "AromaticBonds",
    "Database",
    "Entry",
    "PropertyEntry",
    "Json",
    "Molecule",
    "json_to_rdkit",
    "json_from_rdkit",
]
