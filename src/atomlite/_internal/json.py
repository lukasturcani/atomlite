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
    order: float


class AromaticBond(typing.NamedTuple):
    atom1: int
    atom2: int


Conformer: typing.TypeAlias = list[list[float]]


class Molecule(typing.TypedDict):
    atoms: list[Atom]
    bonds: typing.NotRequired[list[Bond]]
    dative_bonds: typing.NotRequired[list[Bond]]
    aromatic_bonds: typing.NotRequired[list[AromaticBond]]
    properties: typing.NotRequired[dict[str, Json]]
    conformers: typing.NotRequired[list[Conformer]]


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
    bonds = []
    dative_bonds = []
    aromatic_bonds = []
    for bond in molecule.GetBonds():
        match bond.GetBondType():
            case (
                rdkit.BondType.SINGLE
                | rdkit.BondType.DOUBLE
                | rdkit.BondType.TRIPLE
                | rdkit.BondType.QUADRUPLE
                | rdkit.BondType.QUINTUPLE
                | rdkit.BondType.HEXTUPLE
                | rdkit.BondType.ONEANDHALF
                | rdkit.BondType.TWOANDHALF
                | rdkit.BondType.THREEANDHALF
                | rdkit.BondType.FOURANDHALF
                | rdkit.BondType.FIVEANDHALF
            ):
                bonds.append(
                    Bond(
                        atom1=bond.GetBeginAtomIdx(),
                        atom2=bond.GetEndAtomIdx(),
                        order=bond.GetBondTypeAsDouble(),
                    )
                )
            case rdkit.BondType.DATTVE:
                dative_bonds.append(
                    Bond(
                        atom1=bond.GetBeginAtomIdx(),
                        atom2=bond.GetEndAtomIdx(),
                        order=1.0,
                    )
                )
            case rdkit.BondType.AROMATIC:
                aromatic_bonds.append(
                    AromaticBond(bond.GetBeginAtomIdx(), bond.GetEndAtomIdx())
                )
            case _:
                raise RuntimeError("Unsupported bond type")

    d: Molecule = {
        "atoms": [
            Atom(atom.GetAtomicNum(), atom.GetFormalCharge())
            for atom in molecule.GetAtoms()
        ],
    }
    if bonds:
        d["bonds"] = bonds
    if dative_bonds:
        d["dative_bonds"] = dative_bonds
    if aromatic_bonds:
        d["aromatic_bonds"] = aromatic_bonds
    if properties is not None:
        d["properties"] = properties
    if molecule.GetNumConformers() > 0:
        d["conformers"] = [
            conformer.GetPositions().tolist()
            for conformer in molecule.GetConformers()
        ]
    return d


def to_rdkit(molecule: Molecule) -> rdkit.Mol:
    mol = rdkit.EditableMol(rdkit.Mol())
    for atom in molecule["atoms"]:
        rdkit_atom = rdkit.Atom(atom.atomic_number)
        rdkit_atom.SetFormalCharge(atom.charge)
        mol.AddAtom(rdkit_atom)

    for bond in molecule.get("bonds", []):
        mol.AddBond(
            beginAtomIdx=bond.atom1,
            endAtomIdx=bond.atom2,
            order=bond.order,
        )
    for bond in molecule.get("dative_bonds", []):
        mol.AddBond(
            beginAtomIdx=bond.atom1,
            endAtomIdx=bond.atom2,
            order=rdkit.BondType.DATIVE,
        )
    for aromatic_bond in molecule.get("aromatic_bonds", []):
        mol.AddBond(
            beginAtomIdx=aromatic_bond.atom1,
            endAtomIdx=aromatic_bond.atom2,
            order=rdkit.BondType.AROMATIC,
        )

    mol = mol.GetMol()
    if "conformers" in molecule:
        num_atoms = len(molecule["atoms"])
        for conformer in molecule["conformers"]:
            rdkit_conf = rdkit.Conformer(num_atoms)
            for atom_id, atom_coord in enumerate(conformer):
                rdkit_conf.SetAtomPosition(atom_id, atom_coord)
                mol.GetAtomWithIdx(atom_id).SetNoImplicit(True)
            mol.AddConformer(rdkit_conf)
    return mol
