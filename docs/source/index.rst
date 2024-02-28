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
  PropertyEntry <_autosummary/atomlite.PropertyEntry>
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

  We can call :meth:`.Database.get_entries` with no parameters if
  we want to retrieve all the molecules from the database.

.. testcleanup:: adding_molecules

  os.chdir(old_dir)


.. seealso::

  * :class:`.Database`: For additional documentation.
  * :meth:`.Database.add_entries`: For additional documentation.
  * :meth:`.Database.get_entries`: For additional documentation.
  * :meth:`.Entry.from_rdkit`: For additional documentation.
  * :func:`.json_to_rdkit`: For additional documentation.

Adding molecular properties
............................

.. testsetup:: adding_properties

  import atomlite
  db = atomlite.Database(":memory:")
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

.. seealso::

  * :meth:`.Database.add_entries`: For additional documentation.
  * :meth:`.Database.get_entries`: For additional documentation.
  * :meth:`.Entry.from_rdkit`: For additional documentation.

Retrieving molecular properties as a DataFrame
..............................................

.. testsetup:: retrieving_properties

  import atomlite
  db = atomlite.Database(":memory:")
  import rdkit.Chem as rdkit

We can retrieve the properties of molecules as a DataFrame:

.. testcode:: retrieving_properties

  db.add_entries(
      [
          atomlite.Entry.from_rdkit(
              key="first",
              molecule=rdkit.MolFromSmiles("C"),
              properties={"num_atoms": 1, "is_interesting": False},
          ),
          atomlite.Entry.from_rdkit(
              key="second",
              molecule=rdkit.MolFromSmiles("CN"),
              properties={"num_atoms": 2, "is_interesting": True},
          ),
      ]
  )
  print(db.get_property_df(["$.num_atoms", "$.is_interesting"]))

.. testoutput:: retrieving_properties

  shape: (2, 3)
  ┌────────┬─────────────┬──────────────────┐
  │ key    ┆ $.num_atoms ┆ $.is_interesting │
  │ ---    ┆ ---         ┆ ---              │
  │ str    ┆ i64         ┆ bool             │
  ╞════════╪═════════════╪══════════════════╡
  │ first  ┆ 1           ┆ false            │
  │ second ┆ 2           ┆ true             │
  └────────┴─────────────┴──────────────────┘

.. seealso::

  * :meth:`.Database.get_property_df`: For additional documentation.
  * `Valid property paths`_: For a description of the syntax used to
    retrieve properties.

Updating molecular properties
.............................

.. testsetup:: updating_properties

  import atomlite
  db = atomlite.Database(":memory:")
  import rdkit.Chem as rdkit

If we want to update molecular properties, we can use
:meth:`.Database.update_properties`. First, let's
write our initial entry:

.. testcode:: updating_properties

  entry = atomlite.Entry.from_rdkit(
      key="first",
      molecule=rdkit.MolFromSmiles("C"),
      properties={"is_interesting": False},
  )
  db.add_entries(entry)
  for entry in db.get_entries():
      print(entry)

.. testoutput:: updating_properties

  Entry(key='first', molecule={'atomic_numbers': [6]}, properties={'is_interesting': False})

We can change existing properties and add new ones:

.. testcode:: updating_properties

  entry = atomlite.PropertyEntry(
      key="first",
      properties={"is_interesting": True, "new": 20},
  )
  db.update_properties(entry)
  for entry in db.get_entries():
      print(entry)

.. testoutput:: updating_properties

  Entry(key='first', molecule={'atomic_numbers': [6]}, properties={'is_interesting': True, 'new': 20})

Or remove properties:

.. testcode:: updating_properties

  entry = atomlite.PropertyEntry("first", {"new": 20})
  db.update_properties(entry, merge_properties=False)
  for entry in db.get_entries():
      print(entry)

.. testoutput:: updating_properties

   Entry(key='first', molecule={'atomic_numbers': [6]}, properties={'new': 20})

.. note::

   The parameter ``merge_properties=False`` causes the entire property dictionary to
   be replaced for the one in the update.

.. seealso::

  * :meth:`.Database.add_entries`: For additional documentation.
  * :meth:`.Database.get_entries`: For additional documentation.
  * :meth:`.Database.update_properties`: For additional documentaiton.
  * :meth:`.Entry.from_rdkit`: For additional documentation.
  * :class:`.PropertyEntry`: For additional documentation.

Updating entries
................

.. testsetup:: updating_entries

  import atomlite
  import rdkit.Chem as rdkit
  db = atomlite.Database(":memory:")

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

Change existing properties and add new ones:

.. testcode:: updating_entries

  entry = atomlite.Entry.from_rdkit(
      key="first",
      molecule=rdkit.MolFromSmiles("Br"),
      properties={"is_interesting": True, "new": 20},
  )
  db.update_entries(entry)
  for entry in db.get_entries():
      print(entry)

.. testoutput:: updating_entries

   Entry(key='first', molecule={'atomic_numbers': [35]}, properties={'is_interesting': True, 'new': 20})

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

.. seealso::

  * :meth:`.Database.add_entries`: For additional documentation.
  * :meth:`.Database.get_entries`: For additional documentation.
  * :meth:`.Database.update_entries`: For additional documentaiton.
  * :meth:`.Entry.from_rdkit`: For additional documentation.

Checking if a value exists in the database
..........................................

Sometimes you want to use a database as a cache to avoid recomputations.
There is a simple way to do this!

.. testsetup:: check_value_present

  import atomlite
  import rdkit.Chem as rdkit
  db = atomlite.Database(":memory:")
  db.add_entries(
      entries=atomlite.Entry.from_rdkit(
          key="first",
          molecule=rdkit.MolFromSmiles("C"),
      ),
  )

.. testcode:: check_value_present

  molecule = rdkit.MolFromSmiles("CCC")
  num_atoms = db.get_property("first", "$.physical.num_atoms")
  if num_atoms is None:
      num_atoms = molecule.GetNumAtoms()
      db.set_property("first", "$.physical.num_atoms", num_atoms)
  print(num_atoms)

.. testoutput:: check_value_present

  3

.. seealso::

  * :meth:`.Database.get_property`: For additional documentation.
  * :meth:`.Database.set_property`: For additional documentation.
  * :meth:`.Database.get_bool_property`: For type-safe access to boolean properties.
  * :meth:`.Database.set_bool_property`: For type-safe setting of boolean properties.
  * :meth:`.Database.get_int_property`: For type-safe access to integer properties.
  * :meth:`.Database.set_int_property`: For type-safe setting of integer properties.
  * :meth:`.Database.get_float_property`: For type-safe access to float properties.
  * :meth:`.Database.set_float_property`: For type-safe setting of float properties.
  * :meth:`.Database.get_str_property`: For type-safe access to string properties.
  * :meth:`.Database.set_str_property`: For type-safe setting of string properties.

.. _examples-valid-property-paths:

Valid property paths
....................

Given a property dictionary:

.. testcode:: valid_property_paths

  properties = {
      "a": {
          "b": [1, 2, 3],
          "c": 12,
      },
  }

.. testcode:: valid_property_paths
  :hide:

  import atomlite
  import rdkit.Chem as rdkit
  db = atomlite.Database(":memory:")
  db.add_entries(
      entries=atomlite.Entry.from_rdkit(
          key="first",
          molecule=rdkit.MolFromSmiles("C"),
          properties=properties,
      ),
  )

we can access the various properties with the following paths:

.. doctest:: valid_property_paths

  >>> db.get_property("first", "$.a")
  {'b': [1, 2, 3], 'c': 12}
  >>> db.get_property("first", "$.a.b")
  [1, 2, 3]
  >>> db.get_property("first", "$.a.b[1]")
  2
  >>> db.get_property("first", "$.a.c")
  12
  >>> db.get_property("first", "$.a.does_not_exist") is None
  True

A full description of the syntax is provided here_.

.. _here: https://www.sqlite.org/json1.html#path_arguments

.. seealso::

  * :meth:`.Database.get_property`: For additional documentation.

Using an in-memory database
...........................

If you do not wish to write your database to a file, but
only keep it in memory, you can do that with:

.. testcode:: in_memory_database

  import atomlite
  db = atomlite.Database(":memory:")

Running SQL commands
....................

Sometimes you want to alter the database by running some SQL commands
directly, for that, you can use the :attr:`.Database.connection`:

.. testsetup:: running_sql_commands

  import tempfile
  import os
  old_dir = os.getcwd()
  temp_dir = tempfile.TemporaryDirectory()
  os.chdir(temp_dir.name)


.. testcode:: running_sql_commands

  import atomlite
  import rdkit.Chem as rdkit
  db = atomlite.Database("molecules.db")
  entry = atomlite.Entry.from_rdkit("first", rdkit.MolFromSmiles("Br"), {"new": 20})
  db.add_entries(entry)
  for row in db.connection.execute("SELECT * FROM molecules"):
      print(row)

.. testoutput:: running_sql_commands

  ('first', '{"atomic_numbers": [35]}', '{"new": 20}')

.. testcleanup:: running_sql_commands

  os.chdir(old_dir)

Usage with Python versions before 3.11
......................................

Sometimes you have an :mod:`atomlite` database but you can't use :mod:`atomlite`
because it requires Python 3.11, while the project you're trying to use your
database with is stuck at an ealier Python version.

Fortunately, we can still interact with the database, for example here we can
add additional properties to a molecule using just :mod:`sqlite3`:

.. testsetup:: sqlite3_usage

  import tempfile
  import os
  old_dir = os.getcwd()
  temp_dir = tempfile.TemporaryDirectory()
  os.chdir(temp_dir.name)

  import atomlite
  import rdkit.Chem as rdkit
  db = atomlite.Database("molecules.db")
  entry = atomlite.Entry.from_rdkit("first", rdkit.MolFromSmiles("Br"))
  db.add_entries(entry)

.. testcode:: sqlite3_usage

  import sqlite3
  import json
  db = sqlite3.connect("molecules.db")
  db.execute(
      "UPDATE molecules "
      "SET properties=json_patch(properties,?) "
      "WHERE key=?",
      (json.dumps({"new": 20}), "first"),
  )
  db.commit()


We can check that the updates are recognized when using :mod:`atomlite`:

.. testcode:: sqlite3_usage

  import atomlite
  db = atomlite.Database("molecules.db")
  for entry in db.get_entries():
      print(entry)

.. testoutput:: sqlite3_usage

  Entry(key='first', molecule={'atomic_numbers': [35]}, properties={'new': 20})

.. testcleanup:: sqlite3_usage

  os.chdir(old_dir)

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
