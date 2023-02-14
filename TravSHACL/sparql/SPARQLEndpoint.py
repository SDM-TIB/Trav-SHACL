# -*- coding: utf-8 -*-
__author__ = 'Philipp D. Rohde'

import json

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
                json_str = json.loads(self.endpoint.query(query_string).serialize(format='json'))  # FIXME: Serializing the result takes a lot of time
                if isinstance(json_str, dict):
                    return json_str
                else:
                    raise TypeError('JSON was of type ' + type(json_str) + ' instead of dict.')

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
