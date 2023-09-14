#######################
Features of Trav-SHACL
#######################

Prerequisites
=============

The following guides assume:

*   Your shape schema is placed in ``./shapes``
*   There is a SPARQL endpoint running that you can connect to, in this example it is ``http://localhost:14000/sparql``

        +   The endpoint is running in Docker
        +   It is connected to the Docker network ``semantic-web``
        +   Its name is ``endpoint1``
        +   The port ``8890`` of the Docker container is mapped to port ``14000`` of the host

Parameters
=============

*   ``d schemaDir`` (necessary) - path to the directory containing the shape files
*   ``endpoint`` (necessary) - URL of the endpoint the shape schema will be validated against
*   ``graphTraversal`` (necessary) - defines the graph traversal algorithm to be used, is one of ``[BFS, DFS]``
*   ``outputDir`` (necessary) - directory to be used for storing the result files, has to end on ``/``
*   ``--heuristics`` (necessary) - used to determine the seed shape

        +   ``TARGET`` if shapes with a target definition should be prioritized, otherwise omit
        +   prioritize in- or outdegree of shapes, one of ``[IN, OUT]`` or to be omitted
        +   prioritize shapes based on their number of constraints, one of ``[BIG, SMALL]`` or to be omitted
*   ``--selective`` (optional) - use more selective queries for constraint queries
*   ``--orderby`` (optional) - sort the results of all SPARQL queries, ensures the same order in the result logs over several runs
*   ``--outputs`` (optional) - creates one file each for violated and validated targets, otherwise only statistics and traces will be stored
*   ``-m`` (optional) - maximum number of entities in FILTER or VALUES clause of a SPARQL query, default: 256
*   ``-j`` / ``--json`` (optional) - indicates that the SHACL shape schema is expressed in JSON

Properties
==========

The current implementation of Trav-SHACL does not cover all features of the complete SHACL language. The following is a
list of what is supported:

*   simple cardinality constraints, i.e., ``sh:minCount`` and ``sh:maxCount``)
*   relaxed shape-based constraints, i.e., ``sh:qualifiedValueShape`` with ``sh:qualifiedMinCount`` and ``sh:qualifiedMaxCount``
*   simple SPARQL constraints, i.e., ``sh:sparql`` with ``sh:select``

        +   ``sh:prefixes`` is currently not implemented, i.e., the query needs to use full URIs
        +   ``sh:message`` is ignored, i.e., the message is not included in the result
        +   only ``$this`` is supported as placeholder
*   simple logical constraints, i.e., ``sh:or``

The following is a list of some of the more important features that are not yet covered:

*   ``sh:node``
*   ``sh:datatype``
*   ``sh:hasValue``
*   and others