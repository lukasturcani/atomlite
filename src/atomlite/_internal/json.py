import json
import typing

import rdkit.Chem as rdkit

Json: typing.TypeAlias = float | str | None | list["Json"] | dict[str, "Json"]


class Atom(typing.NamedTuple):
    atomic_number: int
    charge: int


class Bond(typing.NamedTuple):
    atom1: int
    atom2: int
    order: int


Conformer: typing.TypeAlias = list[list[float]]


class Molecule(typing.TypedDict):
    atoms: list[Atom]
    bonds: list[Bond]
    properties: typing.NotRequired[dict[str, Json]]
    conformers: typing.NotRequired[list[Conformer]]
    dative_bonds: typing.NotRequired[list[Bond]]


class Entry(dict):
    @staticmethod
    def from_rdkit(
        key: str,
        molecule: rdkit.Mol,
        properties: dict[str, Json] | None = None,
    ) -> "Entry":
        entry = Entry()
        entry["key"] = key
        entry["molecule"] = json.dumps(from_rdkit(molecule, properties))
        return entry

    @property
    def key(self) -> str:
        return self["key"]

    @property
    def molecule(self) -> Molecule:
        return json.loads(self["molecule"])


def from_rdkit(
    molecule: rdkit.Mol,
    properties: dict[str, Json] | None,
) -> Molecule:
    d = {
        "atoms": [
            Atom(atom.GetAtomicNum(), atom.GetFormalCharge())
            for atom in molecule.GetAtoms()
        ],
        "bonds": [
            Bond(
                atom1=bond.GetBeginAtomIdx(),
                atom2=bond.GetEndAtomIdx(),
                order=int(bond.GetBondTypeAsDouble()),
            )
            for bond in molecule.GetBonds()
        ],
    }
    if properties is not None:
        d["properties"] = properties
    if molecule.GetNumConformers() > 0:
        d["conformers"] = [
            conformer.GetPositions().tolist()
            for conformer in molecule.GetConformers()
        ]
    return d


def to_rdkit(molecule: Molecule) -> rdkit.Mol:
    pass
