########################
Features and Limitations
########################

The current implementation of Trav-SHACL does not cover all features of the complete SHACL language.
The following is a list of what is supported:

*   simple cardinality constraints, i.e., ``sh:minCount`` and ``sh:maxCount``
*   relaxed shape-based constraints, i.e., ``sh:qualifiedValueShape`` with ``sh:qualifiedMinCount`` and ``sh:qualifiedMaxCount``
*   simple SPARQL constraints, i.e., ``sh:sparql`` with ``sh:select``

        +   ``sh:prefixes`` is currently not implemented, i.e., the query needs to use full URIs or specify the prefixes within ``sh:select``
        +   ``sh:message`` is ignored, i.e., the message is not included in the result
        +   only ``$this`` is supported as placeholder
*   simple logical constraints, i.e., ``sh:or``

The following is a list of some of the more important features that are not yet covered:

*   ``sh:node``
*   ``sh:datatype``
*   ``sh:hasValue``
*   ``sh:and``
*   and others
