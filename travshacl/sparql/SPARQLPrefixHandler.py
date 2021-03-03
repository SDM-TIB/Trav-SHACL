# -*- coding: utf-8 -*-
"""
For now prefixes used in the definition of SHACL shapes are hardcoded.
TODO: This should be fixed in a later version to facilitate the use of Trav-SHACL.
"""

prefixes = {
    "ub": "<http://swat.cse.lehigh.edu/onto/univ-bench.owl#>",
    "rdf": "<http://www.w3.org/1999/02/22-rdf-syntax-ns#>",
    "dbo": "<http://dbpedia.org/ontology/>",
    "dbr": "<http://dbpedia.org/resource/>",
    "yago": "<http://dbpedia.org/class/yago/>",
    "foaf": "<http://xmlns.com/foaf/0.1/>",
    "": "<http://example.org/>"
}

prefixString = "\n".join(["".join("PREFIX " + key + ":" + value) for (key, value) in prefixes.items()]) + "\n"


def get_prefix_string():
    return prefixString


def get_prefixes():
    return prefixes
