# -*- coding: utf-8 -*-
__author__ = 'Philipp D. Rohde'

from SPARQLWrapper import SPARQLWrapper, JSON
from rdflib import Graph


class SPARQLEndpoint:
    """Implementation of a SPARQL endpoint. This implementation serves as a wrapper in order to be able to execute
       SPARQL queries over SPARQL endpoints via the Web and RDFlib graphs, i.e., in-memory knowledge graphs."""

    instance = None

    class __SPARQLEndpoint:
        """Private class to allow simulation of a Singleton."""
        def __init__(self, endpoint):
            if type(endpoint) == str:
                self.endpoint = SPARQLWrapper(endpoint)
                self.endpoint.setReturnFormat(JSON)
            else:
                self.endpoint = endpoint

        def get_endpoint_type(self):
            return type(self.endpoint)

        def run_query(self, query_string):
            if type(self.endpoint) == SPARQLWrapper:
                self.endpoint.setQuery(query_string)
                return self.endpoint.query().convert()
            else:
                # Use own serialization for the RDFLib graph query result since their serialization is slow.
                # Additionally, we only need the value in the binding; type and datatype are not checked.
                result_raw = self.endpoint.query(query_string)
                variables = result_raw.vars
                result_dict = {
                    'head': {
                        'vars': [v.toPython()[1:] for v in variables]
                    },
                    'results': {
                        'bindings': []
                    }
                }
                for result in result_raw:
                    result_dict['results']['bindings'].append(
                        {var.toPython()[1:]: {'value': result[var].toPython()} for var in variables})
                return result_dict

    def __new__(cls, endpoint):
        if type(endpoint) not in [str, Graph]:
            raise TypeError('The SPARQL endpoint needs retrieve a URL (as string) or an in-memory RDFlib graph. ' +
                            type(endpoint) + ' given instead.')
        if not SPARQLEndpoint.instance:
            SPARQLEndpoint.instance = SPARQLEndpoint.__SPARQLEndpoint(endpoint)
        return SPARQLEndpoint.instance

    def __getattr__(self, item):
        return getattr(self.instance, item)

    def __setattr__(self, key, value):
        return setattr(self.instance, key, value)
