"""Tests for the error reporting of the web interface.

The tests use a small local HTTP server instead of a triple store, so they do not depend on the Docker containers.
"""
import http.server
import socket
import threading
import urllib.error

import pytest

from TravSHACL.app import app as flask_app
from TravSHACL.app import diagnostics

EMPTY_RESULT = b'{"head": {"vars": []}, "results": {"bindings": []}}'
NO_TARGET_SHAPE = """@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix ex: <http://example.org/> .
ex:S a sh:NodeShape ; sh:property [ sh:path ex:p ; sh:minCount 1 ] .
"""


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        path = self.path.split('?')[0]
        status = {'/404': 404, '/401': 401, '/500': 500}.get(path, 200)
        html = path == '/html'
        body = b'<html>not sparql</html>' if html else (EMPTY_RESULT if path == '/ok' else b'error')
        self.send_response(status)
        self.send_header('Content-Type', 'text/html' if html else 'application/sparql-results+json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    do_POST = do_GET


@pytest.fixture(scope='module')
def server():
    httpd = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield 'http://127.0.0.1:' + str(httpd.server_address[1])
    httpd.shutdown()


@pytest.fixture
def client():
    return flask_app.test_client()


@pytest.fixture
def shapes(tmp_path):
    (tmp_path / 'shape.ttl').write_text(NO_TARGET_SHAPE)
    return str(tmp_path)


def post(client, schema, endpoint, **options):
    return client.post('/validate', data={'schemaDir': schema, 'external_endpoint': endpoint, **options})


def free_port():
    with socket.socket() as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


# --- shape schema location ---------------------------------------------------------------------------------------

def test_missing_schema_dir(client, server):
    r = post(client, '', server + '/ok')
    assert r.status_code == 400
    assert b'Shape schema location missing' in r.data


def test_nonexistent_schema_dir(client, server):
    r = post(client, '/does/not/exist', server + '/ok')
    assert r.status_code == 400
    assert b'does not exist' in r.data
    assert b'aria-invalid="true"' in r.data
    assert b'value="/does/not/exist"' in r.data  # input is preserved


def test_schema_dir_is_a_file(client, server, shapes):
    r = post(client, shapes + '/shape.ttl', server + '/ok')
    assert r.status_code == 400
    assert b'is a file' in r.data


def test_schema_dir_without_shapes(client, server, tmp_path):
    (tmp_path / 'readme.txt').write_text('no shapes here')
    r = post(client, str(tmp_path), server + '/ok')
    assert r.status_code == 400
    assert b'No shapes found' in r.data


def test_malformed_shape_file_is_named(client, server, shapes, tmp_path):
    (tmp_path / 'broken.ttl').write_text(NO_TARGET_SHAPE + '\nthis is :: not turtle {{\n')
    r = post(client, shapes, server + '/ok')
    assert r.status_code == 400
    assert b'broken.ttl' in r.data and b'not valid Turtle' in r.data
    assert b'Technical details' in r.data


# --- endpoint ----------------------------------------------------------------------------------------------------

@pytest.mark.parametrize('url', ['example.org/sparql', 'ftp://example.org/sparql', 'http://', 'http://host:port/x'])
def test_invalid_endpoint_url(client, shapes, url):
    r = post(client, shapes, url)
    assert r.status_code == 400
    assert b'Endpoint URL invalid' in r.data


def test_endpoint_refuses_connection(client, shapes):
    r = post(client, shapes, 'http://127.0.0.1:' + str(free_port()) + '/sparql')
    assert r.status_code == 502
    assert b'Endpoint refused the connection' in r.data
    assert b'aria-invalid="true"' in r.data


def test_endpoint_host_not_found(client, shapes):
    r = post(client, shapes, 'http://no-such-host.invalid/sparql')
    assert r.status_code == 502
    assert b'could not be resolved' in r.data


@pytest.mark.parametrize('path, expected', [
    ('/404', b'Endpoint not found'),
    ('/401', b'Endpoint requires authentication'),
    ('/500', b'Endpoint reported an error'),
    ('/html', b'Not a SPARQL endpoint'),
])
def test_endpoint_http_problems(client, shapes, server, path, expected):
    r = post(client, shapes, server + path)
    assert r.status_code == 502
    assert expected in r.data


def test_endpoint_timeout(client, shapes, monkeypatch):
    monkeypatch.setattr(diagnostics, 'ENDPOINT_CHECK_TIMEOUT', 1)
    with socket.socket() as s:  # accepts connections (via the backlog) but never answers
        s.bind(('127.0.0.1', 0))
        s.listen(1)
        r = post(client, shapes, 'http://127.0.0.1:' + str(s.getsockname()[1]) + '/sparql')
    assert r.status_code == 502
    assert b'Endpoint timed out' in r.data


# --- during the validation ---------------------------------------------------------------------------------------

class FakeSchema:
    """Replaces ShapeSchema to simulate failures that only happen once Trav-SHACL is running."""
    init_error = None
    validate_error = None
    kwargs = None

    def __init__(self, **kwargs):
        FakeSchema.kwargs = kwargs
        if FakeSchema.init_error:
            raise FakeSchema.init_error
        self.shapes = []

    def validate(self):
        if FakeSchema.validate_error:
            raise FakeSchema.validate_error
        return {}


@pytest.fixture
def fake_schema(monkeypatch):
    monkeypatch.setattr('TravSHACL.app.ShapeSchema', FakeSchema)
    FakeSchema.init_error = FakeSchema.validate_error = FakeSchema.kwargs = None
    return FakeSchema


def test_unsupported_feature(client, server, shapes, fake_schema):
    fake_schema.init_error = NotImplementedError('unsupported')
    r = post(client, shapes, server + '/ok')
    assert r.status_code == 400
    assert b'Unsupported feature' in r.data and b'Skip and continue' in r.data


def test_ignore_errors_is_passed_on(client, server, shapes, fake_schema):
    assert post(client, shapes, server + '/ok', ignore_errors='yes').status_code == 200
    assert fake_schema.kwargs['ignore_parsing_errors'] is True
    assert post(client, shapes, server + '/ok').status_code == 200
    assert fake_schema.kwargs['ignore_parsing_errors'] is False


def test_endpoint_fails_during_validation(client, server, shapes, fake_schema):
    fake_schema.validate_error = urllib.error.URLError(ConnectionRefusedError(111, 'Connection refused'))
    r = post(client, shapes, server + '/ok')
    assert r.status_code == 502
    assert b'The validation was interrupted' in r.data


def test_unexpected_error(client, server, shapes, fake_schema):
    fake_schema.validate_error = KeyError('missing shape')
    r = post(client, shapes, server + '/ok')
    assert r.status_code == 500
    assert b'Unexpected error' in r.data and b'KeyError' in r.data


def test_invalid_option(client, server, shapes):
    r = post(client, shapes, server + '/ok', max_split_size='abc')
    assert r.status_code == 400
    assert b'Invalid option' in r.data


# --- empty results -----------------------------------------------------------------------------------------------

def test_empty_result_explains_likely_causes(client, server, shapes):
    r = post(client, shapes, server + '/ok')  # the test server has no data; the shape has no target
    assert r.status_code == 200
    assert b'returned no triples' in r.data
    assert b'defines a target' in r.data


def test_escaping_of_error_values(client, server):
    r = post(client, '<script>alert(1)</script>', server + '/ok')
    assert b'<script>alert(1)</script>' not in r.data
    assert b'&lt;script&gt;' in r.data


# --- uploaded shapes file ------------------------------------------------------------------------------------------

def upload(client, endpoint, content, filename='my shapes.ttl', **extra):
    import io
    data = {'external_endpoint': endpoint, 'shapesFile': (io.BytesIO(content), filename), **extra}
    return client.post('/validate', data=data, content_type='multipart/form-data')


@pytest.fixture
def temp_dirs(monkeypatch):
    """Records the temporary directories created for uploads."""
    import tempfile
    created = []
    original = tempfile.mkdtemp

    def recording(*args, **kwargs):
        path = original(*args, **kwargs)
        created.append(path)
        return path

    monkeypatch.setattr('TravSHACL.app.tempfile.mkdtemp', recording)
    return created


def test_upload_is_validated_and_deleted(client, server, temp_dirs):
    import os
    r = upload(client, server + '/ok', NO_TARGET_SHAPE.encode())
    assert r.status_code == 200
    assert b'uploaded file: my shapes.ttl' in r.data
    assert len(temp_dirs) == 1 and not os.path.exists(temp_dirs[0])


def test_upload_is_deleted_after_error(client, server, temp_dirs):
    import os
    r = upload(client, server + '/404', NO_TARGET_SHAPE.encode())
    assert r.status_code == 502
    assert len(temp_dirs) == 1 and not os.path.exists(temp_dirs[0])


def test_upload_malformed_file_is_named_and_deleted(client, server, temp_dirs):
    import os
    r = upload(client, server + '/ok', b'this is :: not turtle {{', filename='broken.ttl')
    assert r.status_code == 400
    assert b'broken.ttl' in r.data and b'not valid Turtle' in r.data
    assert temp_dirs[0].encode() not in r.data  # the temporary path is not leaked
    assert not os.path.exists(temp_dirs[0])


def test_upload_wrong_extension(client, server, temp_dirs):
    import os
    r = upload(client, server + '/ok', b'x', filename='shapes.txt')
    assert r.status_code == 400
    assert b'Unsupported shapes file' in r.data
    assert not os.path.exists(temp_dirs[0])


def test_upload_empty_file(client, server):
    r = upload(client, server + '/ok', b'')
    assert r.status_code == 400
    assert b'Shapes file is empty' in r.data


def test_upload_takes_precedence_over_location(client, server):
    r = upload(client, server + '/ok', NO_TARGET_SHAPE.encode(), schemaDir='/does/not/exist')
    assert r.status_code == 200


def test_upload_filename_cannot_escape_temp_dir(client, server, tmp_path):
    r = upload(client, server + '/ok', NO_TARGET_SHAPE.encode(), filename='../../' + tmp_path.name + '.ttl')
    assert r.status_code == 200
    assert not list(tmp_path.parent.glob(tmp_path.name + '.ttl'))


def test_upload_too_large(client, server, monkeypatch):
    monkeypatch.setitem(flask_app.config, 'MAX_CONTENT_LENGTH', 100)
    r = upload(client, server + '/ok', b'#' * 1000)
    assert r.status_code == 413
    assert b'Shapes file too large' in r.data
