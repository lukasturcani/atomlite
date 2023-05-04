.. atomlite documentation master file, created by
   sphinx-quickstart on Wed May  3 16:47:48 2023.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to atomlite's documentation!
====================================

.. toctree::
  :hidden:
  :maxdepth: 2
  :caption: Contents:

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

First you create a database:

.. testsetup:: quickstart

  import tempfile
  import os
  old_dir = os.getcwd()
  temp_dir = tempfile.TemporaryDirectory()
  os.chdir(temp_dir.name)


.. testcode:: quickstart

  import atomlite
  db = atomlite.Database("molecules.db")

Then you add some molecules and their JSON properties it:

.. testcode:: quickstart

  import rdkit.Chem as rdkit
  mol1 = atomlite.Entry.from_rdkit(
      key="first",
      molecule=rdkit.MolFromSmiles("C"),
      properties={
          "is_interesting": False,
      },
  )
  mol2 = atomlite.Entry.from_rdkit(
      key="second",
      molecule=rdkit.MolFromSmiles("CN"),
      properties={
          "dict_prop": {
            "array_prop": [0, 10, 20.5, "hi"],
          },
      },
  )
  db.add_molecules([mol1, mol2])

And finally you can retrieve the molecules with their keys:

.. testcode:: quickstart

  for key, molecule in db.get_molecules(["first", "second"]):
      rdkit_molecule = atomlite.json_to_rdkit(molecule)
      print(molecule["properties"])

.. testoutput:: quickstart

  {'is_interesting': False}
  {'dict_prop': {'array_prop': [0, 10, 20.5, 'hi']}}


.. testcleanup:: quickstart

  os.chdir(old_dir)



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
