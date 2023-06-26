#######################
Trav-SHACL as a Service
#######################

************
Installation
************

If you want to run Trav-SHACL as a service, you can build the Docker image from its source code or download the Docker image from DockerHub.

Requirements
============

Trav-SHACL is implemented in Python3. The current version supports Python version 3.7 to 3.10.
Trav-SHACL uses the ``rdflib`` library for parsing the SHACL shape schema and the ``SPARQLWrapper`` library for contacting SPARQL endpoints.
The Web API is powered by ``flask``.
In order to run Trav-SHACL as a service, you need to have `Docker <https://docs.docker.com/engine/install/>`_ installed.

Local Source Code
=================

You can install Trav-SHACL from your local source code by performing the following steps.

.. code::

   git clone git@github.com:SDM-TIB/Trav-SHACL.git
   cd Trav-SHACL
   docker build . -t sdmtib/travshacl

DockerHub
=========

The easiest way to install Trav-SHACL is to download the package from PyPI:

.. code::

   docker pull sdmtib/travshacl:latest
