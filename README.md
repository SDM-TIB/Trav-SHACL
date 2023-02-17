[![Tests](https://github.com/SDM-TIB/Trav-SHACL/actions/workflows/test.yml/badge.svg)](https://github.com/SDM-TIB/Trav-SHACL/actions/workflows/test.yml)
[![Latest Release](http://img.shields.io/github/release/SDM-TIB/Trav-SHACL.svg?logo=github)](https://github.com/SDM-TIB/Trav-SHACL/releases)
[![Docker Image](https://img.shields.io/badge/Docker%20Image-sdmtib/travshacl-blue?logo=Docker)](https://hub.docker.com/r/sdmtib/travshacl)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)

[![Python Versions](https://img.shields.io/pypi/pyversions/TravSHACL)](https://pypi.org/project/TravSHACL)
[![Package Format](https://img.shields.io/pypi/format/TravSHACL)](https://pypi.org/project/TravSHACL)
[![Package Status](https://img.shields.io/pypi/status/TravSHACL)](https://pypi.org/project/TravSHACL)
[![Package Version](https://img.shields.io/pypi/v/TravSHACL)](https://pypi.org/project/TravSHACL)

# ![Logo](https://raw.githubusercontent.com/SDM-TIB/Trav-SHACL/master/images/logo.png "Logo")

We present Trav-SHACL, a SHACL engine capable of planning the traversal and execution of a shape schema in a way that invalid entities are detected early and needless validations are minimized.
Trav-SHACL reorders the shapes in a shape schema for efficient validation and rewrites target and constraint queries for fast detection of invalid entities.
The shape schema is validated against an RDF graph accessible via a SPARQL endpoint.

## How to run Trav-SHACL?
If you are looking for **examples** or want to **reproduce the results** reported in our WWW '21 paper, checkout the [**eval-www2021**](https://github.com/SDM-TIB/Trav-SHACL/tree/eval-www2021) **branch**.

**Note:** The current version of Trav-SHACL does not produce a validation report that complies with the SHACL specification.
We will add this feature in the future.

### Prerequisites
The following guides assume:
* Your shape schema is placed in `./shapes`
* There is a SPARQL endpoint running that you can connect to, in this example it is `http://localhost:14000/sparql`
  * The endpoint is running in Docker
  * It is connected to the Docker network `semantic-web`
  * Its name is `endpoint1`
  * The port `8890` of the Docker container is mapped to port `14000` of the host

### Parameters
* `-d schemaDir` (necessary) - path to the directory containing the shape files
* `endpoint` (necessary) - URL of the endpoint the shape schema will be validated against
* `graphTraversal` (necessary) - defines the graph traversal algorithm to be used, is one of `[BFS, DFS]`
* `outputDir` (necessary) - directory to be used for storing the result files, has to end on `/`
* `--heuristics` (necessary) - used to determine the seed shape
  * `TARGET` if shapes with a target definition should be prioritized, otherwise omit
  * prioritize in- or outdegree of shapes, one of `[IN, OUT]` or to be omitted
  * prioritize shapes based on their number of constraints, one of `[BIG, SMALL]` or to be omitted
* `--selective` (optional) - use more selective queries for constraint queries
* `--orderby` (optional) - sort the results of all SPARQL queries, ensures the same order in the result logs over several runs
* `--outputs` (optional) - creates one file each for violated and validated targets, otherwise only statistics and traces will be stored
* `-m` (optional) - maximum number of entities in FILTER or VALUES clause of a SPARQL query, default: 256
* `-j` / `--json` (optional) - indicates that the SHACL shape schema is expressed in JSON

### Features
The current implementation of Trav-SHACL does not cover all features of the complete SHACL language.
The following is a list of what is supported:

- simple cardinality constraints, i.e., `sh:minCount` and `sh:maxCount`)
- relaxed shape-based constraints, i.e., `sh:qualifiedValueShape` with `sh:qualifiedMinCount` and `sh:qualifiedMaxCount`
- simple SPARQL constraints, i.e., `sh:sparql` with `sh:select`
  - `sh:prefixes` is currently not implemented, i.e., the query needs to use full URIs
  - `sh:message` is ignored, i.e., the message is not included in the result
  - only `$this` is supported as placeholder

The following is a list of some of the more important features that are not yet covered:
- `sh:or`
- `sh:node`
- `sh:datatype`
- `sh:value`
- and others

### Run with Docker
In order to connect to the SPARQL endpoint, it must be accessible from within the Docker container.
There shouldn't be anything to configure if you use a public endpoint like DBpedia or Wikidata.
However, if you run your own dockerized SPARQL endpoints, make sure that the endpoint and the Trav-SHACL container are connected to the same Docker network, in this example it is called `semantic-web`.
```bash
# Preparation
docker build -t travshacl .
docker run --name trav-shacl -v $(pwd)/shapes:/shapes -v $(pwd)/results:/results --network=semantic-web -d travshacl

# Run the Validation
docker exec -it trav-shacl bash -c "python3 main.py -d /shapes http://endpoint1:8890/sparql /results/ DFS --heuristics TARGET IN BIG --orderby --selective --outputs"
```

### Run with Python3
```bash
pip3 install -r requirements.txt
python3 main.py -d ./shapes http://localhost:14000/sparql ./results/ DFS --heuristics TARGET IN BIG --orderby --selective --outputs
```

### Trav-SHACL as Python3 Library
Trav-SHACL is available on PyPI, you can install it via the following command:
```bash
python3 -m pip install travshacl
```

After installing Trav-SHACL from PyPI you can use it like in this example:
```python
from TravSHACL import parse_heuristics, GraphTraversal, ShapeSchema

schema_dir = './shapes'
endpoint_url = 'http://localhost:14000/sparql'
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
```

## How to run the Test Suite?
In order to run the test suite, you need to install the production and development dependencies.
```bash
pip3 install -r requirements.txt -r requirements-dev.txt
```
Afterwards, start the Docker container with the test data.
```bash
docker-compose -f tests/docker-compose.yml up -d
```
Finally, you can run the tests by executing the following command.
```bash
pytest
```

## Publications
1. Mónica Figuera, Philipp D. Rohde, Maria-Esther Vidal. Trav-SHACL: Efficiently Validating Networks of SHACL Constraints. In _Proceedings of the Web Conference 2021 (WWW '21), April 19-23, 2021, Ljubljana, Slovenia_. [https://doi.org/10.1145/3442381.3449877](https://doi.org/10.1145/3442381.3449877), [Experiment Scripts](https://github.com/SDM-TIB/Trav-SHACL/tree/eval-www2021), [Preprint](https://arxiv.org/abs/2101.07136)
