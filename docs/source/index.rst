.. atomlite documentation master file, created by
   sphinx-quickstart on Wed May  3 16:47:48 2023.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to atomlite's documentation!
====================================

.. toctree::
  :hidden:
  :maxdepth: 2
  :caption: API:

  Database <_autosummary/atomlite.Database>
  Entry <_autosummary/atomlite.Entry>
  json_from_rdkit <_autosummary/atomlite.json_from_rdkit>
  json_to_rdkit <_autosummary/atomlite.json_to_rdkit>
  Modules <modules>


GitHub: https://github.com/lukasturcani/atomlite

:mod:`atomlite` is a Python library for simple molecular databases on
top of SQLite_. It's goals are as follows:

#. Read and write molecules to SQLite easily.
#. Read and write JSON properties associated with molecules easily.
#. Allow users to interact with the database through SQL commands to fulfil
   more complex use cases.

In other words, :mod:`atomlite` should keep simple interactions with the
database simple, while keeping complex things achievable.

.. _SQLite: https://docs.python.org/3/library/sqlite3.html

For an alternative to :mod:`atomlite`, which provides stronger integration with
RDKit_, and a greater focus on cheminformatics, see chemicalite_.

.. _RDKit: https://www.rdkit.org/
.. _chemicalite: https://github.com/rvianello/chemicalite

Installation
------------

.. code-block:: bash

  pip install atomlite


Getting help
------------

If you get stuck using :mod:`atomlite` I encourage you to get in
touch on Discord (`invite link`_) or by creating an `issue`_ on GitHub.
I'm happy to help!

.. _`invite link`: https://discord.gg/zbCUzuxe2B
.. _`issue`: https://github.com/lukasturcani/atomlite/issues

Quickstart
----------

Adding molecules to the database
................................

.. testsetup:: adding_molecules

  import tempfile
  import os
  old_dir = os.getcwd()
  temp_dir = tempfile.TemporaryDirectory()
  os.chdir(temp_dir.name)

First you create a database:

.. testcode:: adding_molecules

  import atomlite
  db = atomlite.Database("molecules.db")

Then you make some molecular entries:

.. testcode:: adding_molecules

  import rdkit.Chem as rdkit
  entry1 = atomlite.Entry.from_rdkit("first", rdkit.MolFromSmiles("C"))
  entry2 = atomlite.Entry.from_rdkit("second", rdkit.MolFromSmiles("CN"))

And add them to the database:

.. testcode:: adding_molecules

  db.add_entries([entry1, entry2])

Finally, you can retrieve the molecules with their keys:

.. testcode:: adding_molecules

  for entry in db.get_entries(["first", "second"]):
      molecule = atomlite.json_to_rdkit(entry.molecule)
      print(entry.properties)

.. testoutput:: adding_molecules
  :hide:

  {}
  {}

.. tip::

  We can can call ``db.get_entries()`` with no parameters if
  we want to retrieve all the molecules from the database.

.. testcleanup:: adding_molecules

  os.chdir(old_dir)

Adding molecular properties
............................

.. testsetup:: adding_properties

  import tempfile
  import os
  old_dir = os.getcwd()
  temp_dir = tempfile.TemporaryDirectory()
  os.chdir(temp_dir.name)

  import atomlite
  db = atomlite.Database("molecules.db")
  import rdkit.Chem as rdkit

We can add JSON properties to our molecular entries:

.. testcode:: adding_properties

  entry = atomlite.Entry.from_rdkit(
      key="first",
      molecule=rdkit.MolFromSmiles("C"),
      properties={"is_interesting": False},
  )
  db.add_entries(entry)

And retrieve them:

.. testcode:: adding_properties

  for entry in db.get_entries():
      print(entry.properties)

.. testoutput:: adding_properties

  {'is_interesting': False}

.. testcleanup:: adding_properties

  os.chdir(old_dir)

Updating molecular properties
.............................

If we  want to update molecular properties, we

Removing molecular properties
.............................

Updating entries
................

.. testsetup:: updating_entries

  import tempfile
  import os
  old_dir = os.getcwd()
  temp_dir = tempfile.TemporaryDirectory()
  os.chdir(temp_dir.name)

  import atomlite
  db = atomlite.Database("molecules.db")
  import rdkit.Chem as rdkit

We can update whole molecular entries in the database.
Let's write our initial entry:

.. testcode:: updating_entries

  entry = atomlite.Entry.from_rdkit(
      key="first",
      molecule=rdkit.MolFromSmiles("C"),
      properties={"is_interesting": False},
  )
  db.add_entries(entry)
  for entry in db.get_entries():
      print(entry)

.. testoutput:: updating_entries

   Entry(key='first', molecule={'atomic_numbers': [6]}, properties={'is_interesting': False})


We can change the molecule:

.. testcode:: updating_entries

  entry = atomlite.Entry.from_rdkit("first", rdkit.MolFromSmiles("Br"))
  db.update_entries(entry)
  for entry in db.get_entries():
      print(entry)

.. testoutput:: updating_entries

   Entry(key='first', molecule={'atomic_numbers': [35]}, properties={'is_interesting': False})


Add new properties:

.. testcode:: updating_entries

  entry = atomlite.Entry.from_rdkit("first", rdkit.MolFromSmiles("Br"), {"new": 20})
  db.update_entries(entry)
  for entry in db.get_entries():
      print(entry)

.. testoutput:: updating_entries

   Entry(key='first', molecule={'atomic_numbers': [35]}, properties={'is_interesting': False, 'new': 20})

Or remove properties:

.. testcode:: updating_entries

  entry = atomlite.Entry.from_rdkit("first", rdkit.MolFromSmiles("Br"), {"new": 20})
  db.update_entries(entry, merge_properties=False)
  for entry in db.get_entries():
      print(entry)

.. testoutput:: updating_entries

   Entry(key='first', molecule={'atomic_numbers': [35]}, properties={'new': 20})

.. note::

   The parameter ``merge_properties=False`` causes the entire property dictionary to
   be replaced for the one in the update.

.. testcleanup:: updating_entries

  os.chdir(old_dir)

Using an in-memory database
...........................

If you do not wish to write your database to a file, but
only keep it in memory, you can do that with:

.. testcode:: in_memory_database

  import atomlite
  db = atomlite.Database(":memory:")


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
