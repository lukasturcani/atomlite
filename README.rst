:Author: Lukas Turcani
:Docs: https://atomlite.readthedocs.io

========
AtomLite
========

AtomLite is a Python library for simple molecular database on top of SQLite_.

For an alternative to AtomLite, which provides stronger integration with RDKit, and a
greater focus on cheminformatics, see chemicalite_.

.. _SQLite: https://docs.python.org/3/library/sqlite3.html
.. _chemicalite: https://github.com/rvianello/chemicalite


Installation
============

.. code-block:: bash

  pip install atomlite

Quickstart
==========

You can see a lot more examples in our docs_ but here is a taste of using
AtomLite:

.. code-block:: python

  import atomlite
  import rdkit.Chem as rdkit
  # Create a database.
  db = atomlite.Database("molecules.db")
  # Create database entries.
  entry1 = atomlite.Entry.from_rdkit("first", rdkit.MolFromSmiles("C"), {"prop1": "Hi"})
  entry2 = atomlite.Entry.from_rdkit("second", rdkit.MolFromSmiles("CN"), {"prop2": 203})
  # Add entries to database.
  db.add_entries([entry1, entry2])
  # Retrieve entries from database.
  for entry in db.get_entries(["first", "second"]):
    molecule = atomlite.json_to_rdkit(entry.molecule)
    print(entry.properties)


.. _docs: https://atomlite.readthedocs.io
