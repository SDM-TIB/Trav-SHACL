# -*- coding: utf-8 -*-
__author__ = "Philipp D. Rohde"

from SPARQLWrapper import SPARQLWrapper, XML, JSON


class SPARQLEndpoint:
    """Implementation of a SPARQL endpoint; having an URL and the ability to run SPARQL queries."""

    class __SPARQLEndpoint:
        """Private class to allow simulation of a Singleton."""
        def __init__(self, endpointURL):
            self.endpointURL = endpointURL
            self.endpoint = SPARQLWrapper(endpointURL)
            self.endpoint.setReturnFormat(XML)

        def runQuery(self, queryId, queryString, format=None):
            #print("URL:", self.endpointURL)
            #print("query id: ", queryId)
            #print(" - query str: ", queryString)
            self.endpoint.setQuery(queryString)
            if format == 'JSON':
                self.endpoint.setReturnFormat(JSON)
            return self.endpoint.query().convert()

    instance = None

    def __new__(cls, endpointURL):
        if not SPARQLEndpoint.instance:
            SPARQLEndpoint.instance = SPARQLEndpoint.__SPARQLEndpoint(endpointURL)
        return SPARQLEndpoint.instance

    def __getattr__(self, item):
        return getattr(self.instance, item)

    def __setattr__(self, key, value):
        return setattr(self.instance, key, value)
