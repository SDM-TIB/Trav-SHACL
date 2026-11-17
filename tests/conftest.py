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

3. Diagnostics for flaky failures: every query a live-endpoint test sends is recorded
   together with the rows it returned.  If the test fails, the queries are replayed
   against the in-memory graph and the report names those whose rows differ.  A
   difference points at the live endpoint returning unexpected data, no difference
   points at the validation logic itself.
"""
import os
import time
from itertools import islice

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


# --- recording of live-endpoint queries (for the failure report) ---------------------------------
_query_log = []          # (query, bindings) of the current test, live endpoint only
_replay_graph = None
_endpoint_cls = SPARQLEndpoint._SPARQLEndpoint__SPARQLEndpoint
_original_run_query = _endpoint_cls.run_query


def _recording_run_query(self, query_string):
    result = _original_run_query(self, query_string)
    if isinstance(self.endpoint, SPARQLWrapper):
        _query_log.append((query_string, result['results']['bindings']))
    return result


_endpoint_cls.run_query = _recording_run_query


def _rows(bindings):
    """Order-insensitive, type-insensitive representation of a result set."""
    return {frozenset((var, str(cell['value'])) for var, cell in row.items()) for row in bindings}


def _replay_report(max_shown=5) -> str:
    global _replay_graph
    if _replay_graph is None:
        _replay_graph = Graph().parse(TEST_DATA)
    differing = []
    for query, live_bindings in _query_log:
        try:
            result = _replay_graph.query(query)
            graph_bindings = [{str(v)[1:] if str(v).startswith('?') else str(v): {'value': row[v]}
                               for v in result.vars if row[v] is not None} for row in result]
        except Exception as e:  # replay problems must never hide the original failure
            differing.append((query, f'replay failed: {type(e).__name__}: {e}', set(), set()))
            continue
        live, graph = _rows(live_bindings), _rows(graph_bindings)
        if live != graph:
            differing.append((query, None, live - graph, graph - live))

    lines = [f'{len(_query_log)} queries sent to {LIVE_ENDPOINT}; '
             f'{len(differing)} returned different rows than the in-memory graph.']
    for query, error, only_live, only_graph in islice(differing, max_shown):
        lines += ['', query.strip()]
        if error:
            lines.append(error)
        else:
            lines.append(f'  only from live endpoint ({len(only_live)}): {sorted(map(sorted, only_live))[:5]}')
            lines.append(f'  only from in-memory graph ({len(only_graph)}): {sorted(map(sorted, only_graph))[:5]}')
    if not differing:
        lines.append('All replayed queries agree: the live endpoint returned the same rows as the in-memory graph.')
    return '\n'.join(lines)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.when == 'call' and report.failed and _query_log:
        report.sections.append(('SPARQL replay against the in-memory graph', _replay_report()))


@pytest.fixture(autouse=True)
def isolated_sparql_endpoint(request):
    """Make every test build its own endpoint, and wait for the live one if it is used."""
    SPARQLEndpoint.instance = None
    _query_log.clear()
    params = getattr(getattr(request.node, 'callspec', None), 'params', {})
    if params.get('endpoint') == LIVE_ENDPOINT:
        _wait_for_live_endpoint()
    yield
    SPARQLEndpoint.instance = None
