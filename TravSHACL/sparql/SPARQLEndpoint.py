# -*- coding: utf-8 -*-
__author__ = "Philipp D. Rohde"

from SPARQLWrapper import SPARQLWrapper, JSON


class SPARQLEndpoint:
    """Implementation of a SPARQL endpoint; having a URL and the ability to run SPARQL queries."""

    class __SPARQLEndpoint:
        """Private class to allow simulation of a Singleton."""
        def __init__(self, endpoint_url):
            self.endpointURL = endpoint_url
            self.endpoint = SPARQLWrapper(endpoint_url)
            self.endpoint.setReturnFormat(JSON)

        def run_query(self, query_string):
            self.endpoint.setQuery(query_string)
            return self.endpoint.query().convert()

    instance = None

    def __new__(cls, endpoint_url):
        if not SPARQLEndpoint.instance:
            SPARQLEndpoint.instance = SPARQLEndpoint.__SPARQLEndpoint(endpoint_url)
        return SPARQLEndpoint.instance

    def __getattr__(self, item):
        return getattr(self.instance, item)

    def __setattr__(self, key, value):
        return setattr(self.instance, key, value)
