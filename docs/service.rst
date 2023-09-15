#######################
Trav-SHACL as a Service
#######################

*****************
Getting the Image
*****************

If you want to run Trav-SHACL as a service, you can build the Docker image from its source code or download the Docker image from DockerHub.

Requirements
============

Trav-SHACL is implemented in Python3. The current version supports Python version 3.8 to 3.11.
Trav-SHACL uses the ``rdflib`` library for parsing the SHACL shape schema and the ``SPARQLWrapper`` library for contacting SPARQL endpoints.
The Web API is powered by ``flask``.
In order to run Trav-SHACL as a service, you need to have `Docker <https://docs.docker.com/engine/install/>`_ installed.

Local Source Code
=================

You can install Trav-SHACL from your local source code by performing the following steps.

.. code:: bash

   git clone git@github.com:SDM-TIB/Trav-SHACL.git
   cd Trav-SHACL
   docker build . -t sdmtib/travshacl

DockerHub
=========

The easiest method is to download the latest Docker image from DockerHub:

.. code:: bash

   docker pull sdmtib/travshacl:latest
