#######################
Trav-SHACL as a Library
#######################

************
Installation
************

If you want to use Trav-SHACL as a library, you can install it from its source code on GitHub or download the package from PyPI.

Requirements
============

Trav-SHACL is implemented in Python3. The current version supports Python version 3.8 to 3.11.
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

*******
Testing
*******

In order to run the test suite, clone the Trav-SHACL repository from GitHub as explained above (see `Local Source Code`_).
Install the production and development dependencies as shown below.

.. code::

    pip3 install -r requirements.txt -r requirements-dev.txt


Then, start the Docker container with the test data.
If you are changing the host port of the test data container, make sure to also change the port in ``test_cases.py``.
Otherwise, Trav-SHACL cannot connect to the SPARQL endpoint provided by the container and the test suite will fail.

.. code::

    docker-compose -f tests/docker-compose.yml up -d

Finally, run the tests by executing the following command.

.. code::

    pytest

*******
Example
*******

After installing Trav-SHACL as a library, you can use it as shown in the example below:

.. code::

    from TravSHACL import parse_heuristics, GraphTraversal, ShapeSchema

    schema_dir = './shapes'  # shapes folder
    endpoint_url = 'http://localhost:14000/sparql'  #
    graph_traversal = GraphTraversal.DFS  # BFS is also available
    prio_target = 'TARGET'  # shapes with target definition are preferred, alternative value: ''
    prio_degree = 'IN'  # shapes with a higher in-degree are prioritized, alternative value 'OUT'
    prio_number = 'BIG'  # shapes with many constraints are evaluated first, alternative value 'SMALL'
    output_dir = './results/'

    shape_schema = ShapeSchema(
        schema_dir=schema_dir,  # directory where the files containing the shapes definitions are stored
        schema_format='SHACL',  # do not change this value unless you are using the legacy JSON format
        endpoint=endpoint_url,  # the URL of the SPARQL endpoint to be evaluated, alternatively an RDFLib graph can be passed
        graph_traversal=graph_traversal,  # graph traversal algorithm used for planning the shapes order
        heuristics=parse_heuristics(prio_target + ' ' + prio_degree + ' ' + prio_number),  # heuristics to be used for planning the evaluation order
        use_selective_queries=True,  # use more selective constraint queries, alternative value: False
        max_split_size=256,  # maximum number of entities in FILTER or VALUES clause
        output_dir=output_dir,  # directory where the output files will be stored
        order_by_in_queries=False,  # sort the results of SPARQL queries in order to ensure the same order across several runs
        save_outputs=True  # save outputs to output_dir, alternative value: False
        )

    result = shape_schema.validate()  # validate the SHACL shape schema
    print(result)
