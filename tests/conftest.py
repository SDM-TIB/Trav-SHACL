"""Shared pytest fixtures for the Trav-SHACL test suite.

Two problems are addressed here, both of which can make a test outcome depend on
what ran before it instead of on the code under test:

1. ``SPARQLEndpoint`` is a singleton: the endpoint passed to the *first*
   ``ShapeSchema`` of a process is reused for every later one, whatever endpoint
   they ask for.  ``test_case`` is parametrized over the live endpoint and an
   in-memory graph, and pytest runs all live-endpoint tests first, so without a
   reset all "in-memory" tests silently ran against the live endpoint as well.
   The singleton is therefore reset around every test.

2. The live endpoint (Virtuoso in ``tests/docker-compose.yml``) loads its data
   asynchronously after the container starts.  Tests that start before loading has
   finished see partial data and fail, but pass when re-run.  Before the first test
   that uses the live endpoint, we wait until it reports the same number of test
   triples as the in-memory graph.
"""
import os
import time

import pytest
from rdflib import Graph
from SPARQLWrapper import SPARQLWrapper, JSON

from TravSHACL.sparql.SPARQLEndpoint import SPARQLEndpoint

LIVE_ENDPOINT = 'http://localhost:8899/sparql'
TEST_DATA = './tests/data/test.ttl'
TEST_NAMESPACE = 'http://test.example.com/'
# Counts only triples of the test data, so system graphs of the triple store do not matter.
COUNT_QUERY = ('SELECT (COUNT(*) AS ?c) WHERE { ?s ?p ?o . '
               'FILTER(STRSTARTS(STR(?s), "' + TEST_NAMESPACE + '")) }')
WAIT_SECONDS = float(os.environ.get('TRAVSHACL_ENDPOINT_WAIT', '120'))

_live_endpoint_ready = False
_live_endpoint_error = None  # remembered so that only the first test waits out the timeout


def _expected_count() -> int:
    graph = Graph().parse(TEST_DATA)
    return int(next(iter(graph.query(COUNT_QUERY)))[0])


def _live_count() -> int:
    sparql = SPARQLWrapper(LIVE_ENDPOINT)
    sparql.setReturnFormat(JSON)
    sparql.setQuery(COUNT_QUERY)
    return int(sparql.query().convert()['results']['bindings'][0]['c']['value'])


def _wait_for_live_endpoint() -> None:
    global _live_endpoint_ready, _live_endpoint_error
    if _live_endpoint_ready:
        return
    if _live_endpoint_error is not None:
        pytest.fail(_live_endpoint_error, pytrace=False)

    expected = _expected_count()
    deadline = time.monotonic() + WAIT_SECONDS
    last = 'no response'
    while True:
        try:
            count = _live_count()
            if count == expected:
                _live_endpoint_ready = True
                return
            last = f'{count} of {expected} test triples loaded'
        except Exception as e:  # endpoint not up yet / still starting
            last = f'{type(e).__name__}: {e}'
        if time.monotonic() >= deadline:
            _live_endpoint_error = (f'Live endpoint {LIVE_ENDPOINT} not ready after {WAIT_SECONDS:.0f}s ({last}). '
                                    'Is tests/docker-compose.yml running and has the data finished loading?')
            pytest.fail(_live_endpoint_error, pytrace=False)
        time.sleep(1)


@pytest.fixture(autouse=True)
def isolated_sparql_endpoint(request):
    """Make every test build its own endpoint, and wait for the live one if it is used."""
    SPARQLEndpoint.instance = None
    params = getattr(getattr(request.node, 'callspec', None), 'params', {})
    if params.get('endpoint') == LIVE_ENDPOINT:
        _wait_for_live_endpoint()
    yield
    SPARQLEndpoint.instance = None
