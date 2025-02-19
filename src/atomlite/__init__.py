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
    "AromaticBonds",
    "Bonds",
    "Database",
    "Entry",
    "Json",
    "Molecule",
    "PropertyEntry",
    "json_from_rdkit",
    "json_to_rdkit",
]
