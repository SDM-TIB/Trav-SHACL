#######################
Trav-SHACL as a Library
#######################

************
Installation
************

If you want to use Trav-SHACL as a library, you can install it from its source code on GitHub or download the package from PyPI.

Requirements
============

Trav-SHACL is implemented in Python3. The current version supports Python version 3.7 to 3.10.
Trav-SHACL uses the ``rdflib`` library for parsing the SHACL shape schema and the ``SPARQLWrapper`` library for contacting SPARQL endpoints.

Local Source Code
=================

You can install Trav-SHACL from your local source code by performing the following steps.

.. code::

   git clone git@github.com:SDM-TIB/Trav-SHACL.git
   cd Trav-SHACL
   python -m pip install -e .

GitHub
======

Trav-SHACL can also be installed from its source code in GitHub without explicitly cloning the repository:

.. code::

   python -m pip install -e 'git+https://github.com/SDM-TIB/Trav-SHACL#egg=DeTrusty'

PyPI
====

The easiest way to install Trav-SHACL is to download the package from PyPI:

.. code::

   python -m pip install TravSHACL
