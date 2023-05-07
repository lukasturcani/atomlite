import typing

import rdkit.Chem as rdkit

Json: typing.TypeAlias = float | str | None | list["Json"] | dict[str, "Json"]
Conformer: typing.TypeAlias = list[list[float]]


class Bonds(typing.TypedDict):
    """
    JSON representation of bonds.
    """

    atom1: list[int]
    """The indices of the first atom of each bond."""
    atom2: list[int]
    """The indices of the second atom of each bond."""
    order: list[float]
    """The bond order of each bond."""


class AromaticBonds(typing.TypedDict):
    """
    JSON representation of aromatic bonds.
    """

    atom1: list[int]
    """The indices of the first atom of each bond."""
    atom2: list[int]
    """The indices of the second atom of each bond."""


class Molecule(typing.TypedDict):
    """
    A JSON molecule.
    """

    atomic_numbers: list[int]
    """Atomic numbers of atoms in the molecule."""
    atom_charges: typing.NotRequired[list[int]]
    """Charges of atoms in the molecule."""
    bonds: typing.NotRequired[Bonds]
    """Bonds of the molecule."""
    dative_bonds: typing.NotRequired[Bonds]
    """Dative bonds of the molecule."""
    aromatic_bonds: typing.NotRequired[AromaticBonds]
    """Aromatic bonds of the molecule."""
    conformers: typing.NotRequired[list[Conformer]]
    """Conformers of the molecule."""


def json_from_rdkit(molecule: rdkit.Mol) -> Molecule:
    """
    Create a JSON representation of an :mod:`rdkit` molecule.

    Parameters:
        molecule:
            The molecule to convert to JSON.
    Returns:
        A JSON molecule.
    """
    atomic_numbers = []
    atom_charges = []
    save_charges = False
    for atom in molecule.GetAtoms():
        atomic_numbers.append(atom.GetAtomicNum())
        atom_charges.append(atom.GetFormalCharge())
        if atom.GetFormalCharge() != 0:
            save_charges = True

    bonds: Bonds = {
        "atom1": [],
        "atom2": [],
        "order": [],
    }
    dative_bonds: Bonds = {
        "atom1": [],
        "atom2": [],
        "order": [],
    }
    aromatic_bonds: AromaticBonds = {
        "atom1": [],
        "atom2": [],
    }
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
                bonds["atom1"].append(bond.GetBeginAtomIdx())
                bonds["atom2"].append(bond.GetEndAtomIdx())
                bonds["order"].append(bond.GetBondTypeAsDouble())
            case rdkit.BondType.DATTVE:
                dative_bonds["atom1"].append(bond.GetBeginAtomIdx())
                dative_bonds["atom2"].append(bond.GetEndAtomIdx())
                dative_bonds["order"].append(1.0)
            case rdkit.BondType.AROMATIC:
                aromatic_bonds["atom1"].append(bond.GetBeginAtomIdx())
                aromatic_bonds["atom2"].append(bond.GetEndAtomIdx())
            case _:
                raise RuntimeError("Unsupported bond type")

    d: Molecule = {
        "atomic_numbers": atomic_numbers,
    }
    if save_charges:
        d["atom_charges"] = atom_charges
    if bonds["atom1"]:
        d["bonds"] = bonds
    if dative_bonds["atom1"]:
        d["dative_bonds"] = dative_bonds
    if aromatic_bonds["atom1"]:
        d["aromatic_bonds"] = aromatic_bonds
    if molecule.GetNumConformers() > 0:
        d["conformers"] = [
            conformer.GetPositions().tolist()
            for conformer in molecule.GetConformers()
        ]
    return d


def json_to_rdkit(molecule: Molecule) -> rdkit.Mol:
    """
    Create an :mod:`rdkit` molecule from a JSON representation.

    Parameters:
        molecule: The JSON molecule.
    Returns:
        The :mod:`rdkit` molecule.
    """
    mol = rdkit.EditableMol(rdkit.Mol())
    for atomic_number in molecule["atomic_numbers"]:
        rdkit_atom = rdkit.Atom(atomic_number)
        mol.AddAtom(rdkit_atom)

    if "bonds" in molecule:
        for atom1, atom2, order in zip(
            molecule["bonds"]["atom1"],
            molecule["bonds"]["atom2"],
            molecule["bonds"]["order"],
            strict=True,
        ):
            mol.AddBond(atom1, atom2, rdkit.BondType(order))

    if "dative_bonds" in molecule:
        for atom1, atom2 in zip(
            molecule["dative_bonds"]["atom1"],
            molecule["dative_bonds"]["atom2"],
            strict=True,
        ):
            mol.AddBond(atom1, atom2, rdkit.BondType.DATIVE)

    if "aromatic_bonds" in molecule:
        for atom1, atom2 in zip(
            molecule["aromatic_bonds"]["atom1"],
            molecule["aromatic_bonds"]["atom2"],
            strict=True,
        ):
            mol.AddBond(atom1, atom2, rdkit.BondType.AROMATIC)

    mol = mol.GetMol()

    for atom, charge in zip(mol.GetAtoms(), molecule.get("atom_charges", [])):
        atom.SetFormalCharge(charge)

    if "conformers" in molecule:
        num_atoms = len(molecule["atomic_numbers"])
        for conformer in molecule["conformers"]:
            rdkit_conf = rdkit.Conformer(num_atoms)
            for atom_id, atom_coord in enumerate(conformer):
                rdkit_conf.SetAtomPosition(atom_id, atom_coord)
            mol.AddConformer(rdkit_conf)
    return mol
