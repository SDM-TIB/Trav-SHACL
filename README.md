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

![Trav-SHACL Architecture](https://raw.githubusercontent.com/SDM-TIB/Trav-SHACL/master/docs/_images/architecture.png)
Fig. 1: **The Trav-SHACL Architecture (from [1])**

Fig. 1 shows the architecture of Trav-SHACL.
Trav-SHACL receives a SHACL shape schema S and an RDF graph G.
The output of Trav-SHACL are the entities of G that satisfy the shapes in S.
The inter-shape planner uses graph metrics computed over the dependency graph of the shape schema.
It orders the shapes in S in a way that invalid entities are identified as soon as possible.
The intra-shape planner and execution optimizes the target and constraint queries at the time the shape schema is traversed.
So-far (in)validated entities are considered to filter out entities linked to these entities; query rewriting decisions (e.g., pushing filters, partitioning of non-selective queries, and query reordering) are made based on invalid entities' cardinalities and query selectivity.
The rewritten queries are executed against SPARQL endpoints.
The answers of the target and constraint queries as well as the truth value assignments are exchanged during query rewriting and interleaved execution.
They are utilized — in a bottom-up fashion — for constraint rule grounding and saturation.
The intra-shape planner and execution component runs until a fixed-point in the truth value assignments is reached.

If you want to know more, check out the [documentation](https://sdm-tib.github.io/Trav-SHACL/).
The documentation also lists the current [features and limitations](https://sdm-tib.github.io/Trav-SHACL/feature.html).

## How to run Trav-SHACL?
You can use Trav-SHACL as a Python3 library or a Web-based service using Docker.
The documentation includes detailed examples for both scenarios.

* [Trav-SHACL as a Library](https://sdm-tib.github.io/Trav-SHACL/library.html)
* [Trav-SHACL as a Service](https://sdm-tib.github.io/Trav-SHACL/service.html)

## WWW 2021 Evaluation
Trav-SHACL is presented in [1]. If you want to **reproduce the results** reported in our WWW '21 paper, checkout the [**eval-www2021**](https://github.com/SDM-TIB/Trav-SHACL/tree/eval-www2021) **branch**.

## License
Trav-SHACL is licensed under GPL-3.0.

## Publications
1. Mónica Figuera, Philipp D. Rohde, Maria-Esther Vidal. Trav-SHACL: Efficiently Validating Networks of SHACL Constraints. In _Proceedings of the Web Conference 2021 (WWW '21), April 19-23, 2021, Ljubljana, Slovenia_. [https://doi.org/10.1145/3442381.3449877](https://doi.org/10.1145/3442381.3449877), [Experiment Scripts](https://github.com/SDM-TIB/Trav-SHACL/tree/eval-www2021), [Preprint](https://arxiv.org/abs/2101.07136)
