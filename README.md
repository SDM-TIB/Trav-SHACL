# Trav-SHACL Evaluation for WWW2021

## Table of Contents
1. [Preparation of the Environment](#preparation-of-the-environment)
    1. [Machine Requirements](#machine-requirements)
    1. [Libraries](#libraries)
    1. [Bash Commands](#bash-commands)
1. [Experiments](#experiments)
    1. [Research Questions](#research-questions)
    1. [Data](#data)
    1. [Engines](#engines)
    1. [Metrics](#metrics)
    1. [Setups](#setups)
    1. [How to reproduce?](#how-to-reproduce)
1. [Q&A](#QA)

## Preparation of the Environment
### Machine Requirements
- OS: Ubuntu 18.04.4 LTS
- CPU: Intel Xeon E5-1630v4 (4 cores @ 3.7 GHz)
- Memory: 64 GiB DDR4
- HDD: approx. 200 GiB free disk space

### Libraries
- Docker - v19.03.6 or newer
- docker-compose - v1.26.0 or newer

### Bash Commands
- wget
- unzip
- logname
- sh -c "sync; echo 3 > /proc/sys/vm/drop_caches"


## Experiments
### Research Questions
1. What is the effect of validating the shapes following different traversal strategies?
2. Can the knowledge gained from previously validated shapes be exploited to improve the performance?
3. What is the impact of the size of the data sources, i.e., do the approaches scale up?
4. What is the impact of the topology of the constraint network and the selectivity of the shapes?

### Data
To the best of our knowledge, there are no benchmarks to evaluate the performance of SHACL validators.
Therefore, we built our test beds based on the accepted and commonly used [Lehigh University Benchmark (LUBM)](http://swat.cse.lehigh.edu/projects/lubm/).
The LUBM Data Generator was used to create data of different sizes; the small, medium, and large knowledge graphs.
We created one shape per class in the data (schema 3).
Schemas 1 and 2 are subsets of schema 3 with schema 1 being a subset of schema 2.
The originally generated data is modified in such a way that for each of the shape schemas each knowledge graph size has three different percentages of invalid entities.
The data used in the evaluation of our proposed approach can be downloaded from the [Data Repository of the Leibniz University of Hannover, Germany](https://data.uni-hannover.de/dataset/trav-shacl-benchmarks-experimental-settings-and-evaluation).

### Engines
We compare our approach with the state of the art, namely SHACL2SPARQL.
Due to performance differences in Java and Python, we additionally consider a Python implementation of SHACL2SPARQL as baseline, called SHACL2SPARQL-py.
Furthermore, we study the behavior of nine different configurations of our approach (as in the table below).
This leads to a comparison of a total of eleven engines.

<table>
  <tr>
    <th rowspan=2>Name</th>
    <th rowspan=2>Traversal Strategy</th>
    <th colspan=2>Seed Shape Selection</th>
  </tr>
  <tr>
    <th>Connectivity</th>
    <th>Constraints</th>
  </tr>
  <tr>
    <td>Trav-SHACL 1</td>
    <td>BFS</td>
    <td>high indegree</td>
    <td>many</td>
  </tr>
  <tr>
    <td>Trav-SHACL 2</td>
    <td>BFS</td>
    <td>high indegree</td>
    <td>few</td>
  </tr>
  <tr>
    <td>Trav-SHACL 3</td>
    <td>BFS</td>
    <td>high outdegree</td>
    <td>many</td>
  </tr>
  <tr>
    <td>Trav-SHACL 4</td>
    <td>BFS</td>
    <td>high outdegree</td>
    <td>few</td>
  </tr>  <tr>
    <td>Trav-SHACL 5</td>
    <td>DFS</td>
    <td>high indegree</td>
    <td>many</td>
  </tr>
  <tr>
    <td>Trav-SHACL 6</td>
    <td>DFS</td>
    <td>high indegree</td>
    <td>few</td>
  </tr>
  <tr>
    <td>Trav-SHACL 7</td>
    <td>DFS</td>
    <td>high outdegree</td>
    <td>many</td>
  </tr>
  <tr>
    <td>Trav-SHACL 8</td>
    <td>DFS</td>
    <td>high outdegree</td>
    <td>few</td>
  </tr>
  <tr>
    <td>Trav-SHACL 9</td>
    <td colspan=3 align="center">random</td>
  </tr>
</table>

### Metrics
We report the following metrics:
- _Average Validation Time_: Average time (in seconds) elapsed between starting the validation of a data set and the engine finishing the validation.
- _Standard Deviation_: The standard deviation of the validation time.
- _dief@t_: A measurement for the continuous efficiency of an engine in the first t time units of the validation.

### Setups
The combination of the data sets, shape schemas, and engines leads to a total of 297 experiments.
Each of the experiments is run five times.
All caches are flushed between two consecutive experiments.

### How to reproduce?
In order to facilitate the reproduction of the results, we encapsulated all components in Docker containers and wrote Shell scripts for the different steps:
- `01_preparations.sh` downloading the data and preparing the Docker environment
- `02_experiments.sh` runs all 297 experiments with five runs each; flushes all caches between experiments (needs `sudo`)
- `03_results.sh` generates the plots once the experiments are done
- `04_cleanup.sh` cleans up the Docker environment and changes ownership of the plots to the caller (were owned by `root` due to Docker)

All scripts require `sudo` access if your user requires `sudo` to run Docker commands.
Script 2 and 4 _always_ need `sudo` access to flush the caches or changing the file owner respectively.

You can run the entire pipeline by typing
```bash
sudo ./00_automatic.sh
```

However, if you like to check the progress between the steps on your own, you can run each script after each other.
**We recommend running the scripts manually after each other.**

1. `sudo ./01_preparations.sh` could take some time due to building the Docker images; but we do not expect any issues here
1. `sudo ./02_experiments.sh` running this script will take a lot of time; for us it took about a week +/- a day.
Once the script is done, the directory `results` should contain the following directories/data:
    - `shacl2sparql` contains all results produced by SHACL2SPARQL
    - `shacl2sparqlpy` contains all results produced by SHACL2SPARQL-py
    - `travshacl` contains all results produced by the various configurations of Trav-SHACL
Make sure to check if any errors are logged in the according error logs.
1. `sudo ./03_results.sh` if all experiment results are present, there are no issues to be expected here; however, running the script may take about 30-40 minutes. The directory `results` now should also contain the additional directories/data:
    - `dief_data` contains data necessary for generating the plots showing the continuous behavior
    - `plots` directory for the plots
        - `dieft` contains all _dief@t_ plots
        - `time` contains all _validation time_ plots
        - `traces` contains all _answer trace_ plots
    - `results.tsv` summary of _validation time_ results of all experiments
1. `sudo ./04_cleanup.sh` deleting Docker images and containers, changing ownership of the result plots to the user running the script as they are owned by `root` due to the use of Docker

## Q&A
>Q: Some result files are empty.

>A: It may happen that one (or more) of the endpoints stop responding during query execution. Unfortunately, we were not able to find out why this happens. However, those errors seem to be rare. However, it looks like SHACL2SPARQL is the engine mainly causing issues with the endpoints. There should be an entry in the according error log. It is necessary to restart the evaluation of the experiments that failed.
<hr>

>Q: The plot generation encounters an error during summarizing the execution times.

>A: It is very likely that this issue is linked to the above-mentioned one. Please, check which experiments failed to produce the necessary output and restart them.

