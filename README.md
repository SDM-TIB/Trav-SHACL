# Trav-SHACL

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
  * At the moment Trav-SHACL only parses SHACL shapes in JSON format, see the `eval-www2021` branch for an example
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
* `--outputs` (optional) - creates one file each for violated and validated targets, otherwise only statistics and traces will be stored
* `-m` (optional) - maximum number of entities in FILTER or VALUES clause of a SPARQL query, default: 256

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

## Publications
1. Mónica Figuera, Philipp D. Rohde, Maria-Esther Vidal. Trav-SHACL: Efficiently Validating Networks of SHACL Constraints. In _Proceedings of the Web Conference 2021 (WWW '21), April 19-23, 2021, Ljubljana, Slovenia_. [Experiment Scripts](https://github.com/SDM-TIB/Trav-SHACL/tree/eval-www2021), [Preprint](https://arxiv.org/abs/2101.07136)