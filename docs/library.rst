.. |python| image:: https://img.shields.io/pypi/pyversions/TravSHACL
.. |format| image:: https://img.shields.io/pypi/format/TravSHACL
.. |status| image:: https://img.shields.io/pypi/status/TravSHACL
.. |version| image:: https://img.shields.io/pypi/v/TravSHACL
   :target: https://pypi.org/project/TravSHACL

|python| |format| |status| |version|

#######################
Trav-SHACL as a Library
#######################

************
Installation
************

If you want to use Trav-SHACL as a library, you can install it from its source code on GitHub or download the package from PyPI.

Requirements
============

Trav-SHACL is implemented in Python3.
The current version supports |python|.
Trav-SHACL uses the ``rdflib`` library for parsing the SHACL shape schema and the ``SPARQLWrapper`` library for contacting SPARQL endpoints.

Local Source Code
=================

You can install Trav-SHACL from your local source code by performing the following steps.

.. code:: bash

   git clone git@github.com:SDM-TIB/Trav-SHACL.git
   cd Trav-SHACL
   python -m pip install -e .

GitHub
======

Trav-SHACL can also be installed from its source code in GitHub without explicitly cloning the repository:

.. code:: bash

   python -m pip install -e 'git+https://github.com/SDM-TIB/Trav-SHACL#egg=DeTrusty'

PyPI
====

The easiest way to install Trav-SHACL is to download the package from PyPI:

.. code:: bash

   python -m pip install TravSHACL

*******
Testing
*******

In order to run the test suite, clone the Trav-SHACL repository from GitHub as explained above (see `Local Source Code`_).
Install the production and development dependencies as shown below.

.. code:: bash

    pip3 install -r requirements.txt -r requirements-dev.txt


Then, start the Docker container with the test data.
If you are changing the host port of the test data container, make sure to also change the port in ``test_cases.py``.
Otherwise, Trav-SHACL cannot connect to the SPARQL endpoint provided by the container and the test suite will fail.

.. code:: bash

    docker-compose -f tests/docker-compose.yml up -d

Finally, run the tests by executing the following command.

.. code:: bash

    pytest

*******
Example
*******

You can run Trav-SHACL over example data provided in the GitHub repository.
While it is necessary to clone the repository (or download the example folder) from GitHub, you can still install Trav-SHACL from PyPI.
Note that you might want to create a virtual environment for Trav-SHACL.
In order to serve the example data, you need to have `Docker <https://docs.docker.com/engine/install/>`_ installed.

Preparing the Data
==================

Assuming your current working directory contains the ``example`` folder, you can start the Docker container serving the SPARQL endpoint with the example data as shown below:

.. code:: bash

   docker-compose -f ./example/docker-compose.yml up -d example_data

.. NOTE::

   The SPARQL endpoint might take a few seconds in order to be started.
   You can check its accessibility by navigating to `http://localhost:9090/sparql <http://localhost:9090/sparql>`_

Code
====

Now the data is accessible and you can validate it against the provided example shapes.

.. code:: python3

    from TravSHACL import parse_heuristics, GraphTraversal, ShapeSchema

    prio_target = 'TARGET'  # shapes with target definition are preferred, alternative value: ''
    prio_degree = 'IN'  # shapes with a higher in-degree are prioritized, alternative value 'OUT'
    prio_number = 'BIG'  # shapes with many constraints are evaluated first, alternative value 'SMALL'

    shape_schema = ShapeSchema(
        schema_dir='./shapes/LUBM',
        endpoint='http://localhost:9090/sparql',
        graph_traversal=GraphTraversal.DFS,
        heuristics=parse_heuristics(prio_target + ' ' + prio_degree + ' ' + prio_number),
        use_selective_queries=True,
        max_split_size=256,
        output_dir='./result/',  # directory where the output files will be stored
        order_by_in_queries=False,  # sort the results of SPARQL queries in order to ensure the same order across several runs
        save_outputs=True  # save outputs to output_dir, alternative value: False
    )

    result = shape_schema.validate()  # validate the SHACL shape schema
    print(result)

.. NOTE::

   All parameters of ``ShapeSchema`` are keyword-only. The only required parameters are ``schema_dir`` and ``endpoint``.

Parameters
==========

Before executing the above script, let us have a look at the different parameters.

* ``schema_dir`` path to the directory containing the shape files
* ``endpoint`` URL of the endpoint to evaluated; alternatively, an RDFLib graph can be passed
* ``graph_traversal`` (optional) defines the graph traversal algorithm to be used, is one of ``[GraphTraversal.BFS, GraphTraversal.DFS]``; default: ``GraphTraversal.DFS``
* ``heuristics`` (optional) used to determine the seed shape. Use the method ``parse_heuristics`` with a string in order to set the desired heuristics; default: ``parse_heuristics('TARGET IN BIG')``.

   + ``TARGET`` if shapes with a target definition should be prioritized, otherwise omit
   + prioritize in- or outdegree of shapes, one of ``[IN, OUT]`` or to be omitted
   + prioritize shapes based on their number of constraints, one of ``[BIG, SMALL]`` or to be omitted
* ``use_selective_queries`` (optional) use more selective constraint queries, is one of ``[True, False]``; default: ``True``
* ``max_split_size`` (optional) maximum number of entities in FILTER or VALUES clause of a SPARQL query; default: ``256``
* ``output_dir`` (optional) directory where the output files will be stored; default: ``None``
* ``order_by_in_queries`` (optional) sort the results of all SPARQL queries, ensures the same order in the result logs over several runs, is one of ``[True, False]``; default: ``False``
* ``save_outputs`` (optional) creates one file each for violated and validated targets, otherwise only statistics and traces will be stored, is one of ``[True, False]``; default: ``False``

Results: Internal Structure
===========================

Executing the above code from within the ``example`` folder will print the validation result using the internal representation.
More insights can be found in the various files that are generated in ``result``.
Let us discuss the printed result first.

.. code:: text

  {
    '<http://example.org/GraduateCourseShape>': {
      'valid_instances': {
        ('<http://example.org/FullProfessorShape>', 'http://www.Department0.University0.edu/FullProfessor9', True),
        ('<http://example.org/GraduateCourseShape>', 'http://www.Department0.University0.edu/GraduateCourse3', True),
        ('<http://example.org/GraduateCourseShape>', 'http://www.Department0.University0.edu/GraduateCourse16', True)
        ('<http://example.org/GraduateCourseShape>', 'http://www.Department0.University0.edu/GraduateCourse33', True),
        ('<http://example.org/GraduateCourseShape>', 'http://www.Department0.University0.edu/GraduateCourse42', True),
        ('<http://example.org/GraduateStudentShape>', 'http://www.Department0.University0.edu/GraduateStudent0', True),
        ('<http://example.org/GraduateStudentShape>', 'http://www.Department0.University0.edu/GraduateStudent91', True),
        ('<http://example.org/FullProfessorShape>', 'http://www.Department9.University0.edu/FullProfessor1', True),
        ('<http://example.org/GraduateCourseShape>', 'http://www.Department9.University0.edu/GraduateCourse1', True),
        ('<http://example.org/GraduateStudentShape>', 'http://www.Department9.University0.edu/GraduateStudent28', True)
      },
     'invalid_instances': {
        ('<http://example.org/GraduateStudentShape>', 'http://www.Department9.University0.edu/GraduateStudent5', True)
      }
    },
    '<http://example.org/UniversityShape>': {
      'valid_instances': {
        ('<http://example.org/DepartmentShape>', 'http://www.Department0.University0.edu', True),
        ('<http://example.org/DepartmentShape>', 'http://www.Department1.University0.edu', True),
        ('<http://example.org/DepartmentShape>', 'http://www.Department9.University0.edu', True),
        ('<http://example.org/UniversityShape>', 'http://www.University0.edu', True)
      },
      'invalid_instances': {
          ('<http://example.org/UniversityShape>', 'http://www.University1.edu', True),
          ('<http://example.org/UniversityShape>', 'http://www.University2.edu', True),
          ('<http://example.org/UniversityShape>', 'http://www.University3.edu', True),
          ('<http://example.org/UniversityShape>', 'http://www.University4.edu', True)
      }
    },
    '<http://example.org/DepartmentShape>': {
      'valid_instances': set(),
      'invalid_instances': set()
    },
    '<http://example.org/GraduateStudentShape>': {
      'valid_instances': set(),
      'invalid_instances': {
        ('<http://example.org/GraduateStudentShape>', 'http://www.Department2.University0.edu/GraduateStudent7', True)
      }
    },
    '<http://example.org/FullProfessorShape>': {
      'valid_instances': set(),
      'invalid_instances': {
        ('<http://example.org/FullProfessorShape>', 'http://www.Department1.University0.edu/FullProfessor0', True),
        ('<http://example.org/FullProfessorShape>', 'http://www.Department2.University0.edu/FullProfessor2', True),
        ('<http://example.org/FullProfessorShape>', 'http://www.Department5.University0.edu/FullProfessor3', True)
      }
    },
    'unbound': {
      'valid_instances': set()
    }
  }

The keys of the dictionary correspond to the names of the validated shapes.
For each shape, Trav-SHACL records the entities that have either been validated (``valid_instances``) or violated (``invalid_instances``).
Such a record is a tuple containing the name of the shape which the entity belongs to, the identifier of the entity itself, and ``True``.
Trav-SHACL keeps this structure since the validation result of an entity may rely on the satisfaction of an entity from another shape.
If the other entity has not yet been validated, the validation is postponed until the needed validation result is available.
After evaluating all shapes, entities with pending decisions are marked as valid since no violations were found.
These entities are recorded in ``unbound``.

Results: Output Files
=====================

Additionally, Trav-SHACL stores the following files:

* ``stats.txt`` contains statistics about the validation, like

   + number of targets
   + number of valid targets
   + number of invalid targets
   + number of executed queries
   + number of generated rules
   + maximum query execution time (in ms)
   + total query execution time (in ms)
   + total saturation time (in ms)
   + total validation time (in ms)
* ``targets_valid.log`` contains all valid targets (one per line) in the form `shape_name`(`entity`)
* ``targets_invalid.log`` contains all invalid targets (one per line) in the form `shape_name`(`entity`)
* ``validation.log`` log file containing the node order, executed queries, etc.
* ``validationReport.ttl`` a validation report in Turtle format that adheres to the SHACL specification
