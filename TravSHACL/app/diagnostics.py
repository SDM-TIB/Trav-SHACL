"""Checks and error explanations for the web interface.

The checks run before the (potentially long) validation starts and fail fast with a message that tells the user
what is wrong and how to fix it. The explanations translate exceptions raised by the libraries during the
validation into the same kind of message.
"""
import http.client
import os
import re
import socket
import ssl
import urllib.error
from urllib.parse import urlsplit

from rdflib import Graph
from werkzeug.utils import secure_filename
from SPARQLWrapper import SPARQLWrapper, JSON
from SPARQLWrapper.SPARQLExceptions import SPARQLWrapperException, Unauthorized, EndPointNotFound, QueryBadFormed

from TravSHACL.core.ShapeParser import ShapeParser

# Seconds to wait for the endpoint when checking its availability before the validation starts.
try:
    ENDPOINT_CHECK_TIMEOUT = int(os.environ.get('ENDPOINT_CHECK_TIMEOUT', '10'))
except ValueError:
    ENDPOINT_CHECK_TIMEOUT = 10

IN_DOCKER = os.path.exists('/.dockerenv')
LOCAL_HOSTS = ('localhost', '127.0.0.1', '::1', '0.0.0.0')


class UserFacingError(Exception):
    """An error that is shown to the user in the web interface.

    :param title: short summary of the problem
    :param message: what went wrong
    :param hint: what the user can do about it
    :param field: name of the form field the problem is caused by, if any
    :param status: HTTP status code of the response
    :param details: technical details, e.g., the original exception message
    """

    def __init__(self, title, message, hint=None, field=None, status=400, details=None):
        super().__init__(message)
        self.title = title
        self.message = message
        self.hint = hint
        self.field = field
        self.status = status
        self.details = details


# ---------------------------------------------------------------------------------------------------------------------
# shape schema location
# ---------------------------------------------------------------------------------------------------------------------

def find_shape_files(path):
    """Returns the shape files (*.ttl) in the directory and its subdirectories; same lookup as Trav-SHACL itself."""
    extension = ShapeParser.get_file_extension('SHACL')
    return [os.path.join(root, file)
            for root, _, files in os.walk(path)
            for file in files
            if os.path.splitext(file)[1].lower() == extension]


def save_uploaded_shapes(files, directory):
    """Stores the uploaded shapes files in the given (temporary) directory.

    The files are stored under a sanitized name with a running number as prefix. The latter keeps files with the
    same name apart, the former rules out path traversal via the name sent by the client.

    :param files: the uploaded files (list of werkzeug FileStorage)
    :param directory: directory the files are saved to
    :return: dict mapping the stored file name to the name of the file as uploaded
    """
    field = 'shapesFile'
    extension = ShapeParser.get_file_extension('SHACL')
    names = {}
    for index, file in enumerate(files, start=1):
        original = os.path.basename((file.filename or '').replace('\\', '/'))
        if os.path.splitext(original)[1].lower() != extension:
            raise UserFacingError('Unsupported shapes file',
                                  'The file "' + original + '" is not a Turtle file.',
                                  hint='Upload SHACL shapes in Turtle syntax, i.e., files with the extension '
                                       + extension + '.',
                                  field=field)
        stored = '{:03d}_{}'.format(index, secure_filename(original) or 'shapes' + extension)
        target = os.path.join(directory, stored)
        file.save(target)
        if os.path.getsize(target) == 0:
            raise UserFacingError('Shapes file is empty', 'The file "' + original + '" has no content.', field=field)
        names[stored] = original
    return names


def check_schema_dir(path):
    """Makes sure the shape schema location exists, is readable, and contains shapes."""
    field = 'schemaDir'
    if not path:
        raise UserFacingError('Shape schema location missing',
                              'Enter the path to the directory that contains your SHACL shapes.', field=field)
    if not os.path.exists(path):
        hint = ('Paths are resolved inside the Docker container. Mount your shapes into the container, for example '
                'with "-v ./shapes:/shapes", and enter the path as seen from inside the container.'
                if IN_DOCKER else
                'The path is resolved on the machine that runs Trav-SHACL, not on the machine of your browser.')
        raise UserFacingError('Shape schema location not found', 'The path "' + path + '" does not exist.',
                              hint=hint, field=field)
    if not os.path.isdir(path):
        raise UserFacingError('Shape schema location is not a directory',
                              '"' + path + '" is a file. Trav-SHACL expects a directory with one or more .ttl files.',
                              field=field)
    if not os.access(path, os.R_OK | os.X_OK):
        raise UserFacingError('Shape schema location not readable',
                              'Trav-SHACL is not allowed to read the directory "' + path + '".',
                              hint='Check the permissions of the directory.', field=field)
    if not find_shape_files(path):
        raise UserFacingError('No shapes found',
                              'The directory "' + path + '" does not contain any .ttl files.',
                              hint='Shapes have to be stored as Turtle files with the extension .ttl, one or more '
                                   'per directory. Subdirectories are searched as well.',
                              field=field)


def find_unparsable_file(path):
    """Parses the shape files one by one. Returns (file, exception) for the first that fails, None if all parse."""
    for file in find_shape_files(path):
        try:
            Graph().parse(file)
        except Exception as e:  # any parser or I/O problem identifies the file
            return file, e
    return None


def _summarize_parse_error(exc):
    """Extracts the reason and line number from the (verbose) message of rdflib's syntax errors."""
    if isinstance(exc, OSError):
        return exc.strerror or str(exc)
    text = str(exc)
    reason = re.search(r'Bad syntax \((.*?)\) at', text, re.S)
    line = re.search(r'at line (\d+)', text)
    if reason and line:
        return reason.group(1) + ' (near line ' + line.group(1) + ')'
    if reason:
        return reason.group(1)
    return text.strip().splitlines()[0] if text.strip() else exc.__class__.__name__


# ---------------------------------------------------------------------------------------------------------------------
# SPARQL endpoint
# ---------------------------------------------------------------------------------------------------------------------

def check_endpoint(url):
    """Makes sure the URL is well-formed and that a SPARQL endpoint answers there.

    :return: whether the endpoint returned any triples
    """
    field = 'external_endpoint'
    if not url:
        raise UserFacingError('Endpoint missing', 'Enter the URL of the SPARQL endpoint.', field=field)
    try:
        parts = urlsplit(url)
        _ = parts.port  # raises ValueError for an invalid port
    except ValueError:
        parts = None
    if parts is None or parts.scheme not in ('http', 'https') or not parts.hostname:
        raise UserFacingError('Endpoint URL invalid',
                              '"' + url + '" is not a valid endpoint URL.',
                              hint='Enter the complete URL, starting with http:// or https://, '
                                   'for example https://example.org/sparql.',
                              field=field)

    try:
        wrapper = SPARQLWrapper(url)
        wrapper.setReturnFormat(JSON)
        wrapper.setTimeout(ENDPOINT_CHECK_TIMEOUT)
        wrapper.setQuery('SELECT * WHERE { ?s ?p ?o } LIMIT 1')
        result = wrapper.query().convert()
    except Exception as e:  # all problems are explained to the user
        raise explain_endpoint_error(e, url) from e

    if not (isinstance(result, dict) and 'results' in result):
        raise UserFacingError('Not a SPARQL endpoint',
                              'The server at ' + url + ' answered, but not with SPARQL query results.',
                              hint='The URL probably points to a web page instead of the SPARQL service. '
                                   'Many triple stores provide the service at a path ending in /sparql.',
                              field=field, status=502)
    return bool(result['results']['bindings'])


def is_endpoint_error(exc):
    """Whether the exception is a typical result of talking to a SPARQL endpoint."""
    return isinstance(exc, (SPARQLWrapperException, OSError, http.client.HTTPException))


def explain_endpoint_error(exc, url, during_validation=False):
    """Translates an exception raised while contacting the endpoint into a message for the user."""
    field = 'external_endpoint'
    parts = urlsplit(url)
    host = parts.hostname or url
    try:
        where = host + (':' + str(parts.port) if parts.port else '')
    except ValueError:
        where = host
    details = exc.__class__.__name__ + ': ' + str(exc)
    reason = exc.reason if isinstance(exc, urllib.error.URLError) else None
    local = host in LOCAL_HOSTS

    def error(title, message, hint=None):
        if during_validation:
            message = 'The validation was interrupted. ' + message
        return UserFacingError(title, message, hint=hint, field=field, status=502, details=details)

    reachability_hint = 'Check that the endpoint is running and that host and port are correct.'
    if IN_DOCKER:
        if local:
            reachability_hint = ('Inside a Docker container, "' + host + '" refers to the container itself. Use the '
                                 'name of the endpoint\'s container (both containers need to be in the same Docker '
                                 'network) or host.docker.internal for a service on the Docker host.')
        else:
            reachability_hint = ('Check that the endpoint is running. If it runs in another Docker container, both '
                                 'containers need to be in the same Docker network, and the URL has to use the name of '
                                 'the container and the port inside that network, not the port published to the host.')

    if isinstance(exc, Unauthorized) or (isinstance(exc, urllib.error.HTTPError) and exc.code in (401, 403)):
        return error('Endpoint requires authentication',
                     'The endpoint at ' + url + ' denied access.',
                     'The web interface does not support credentials. Use an endpoint that can be queried without '
                     'authentication or use Trav-SHACL as a library with endpoint_user and endpoint_password.')
    if isinstance(exc, EndPointNotFound) or (isinstance(exc, urllib.error.HTTPError) and exc.code == 404):
        return error('Endpoint not found',
                     'The server is reachable, but there is no SPARQL service at ' + url + ' (HTTP 404).',
                     'Check the path of the URL. Many triple stores provide the service at a path ending in /sparql.')
    if isinstance(exc, QueryBadFormed):
        return error('Endpoint rejected the request',
                     'The endpoint at ' + url + ' answered a simple SPARQL query with HTTP 400.',
                     'Check that the URL points to the query endpoint of a SPARQL service.')
    if isinstance(exc, urllib.error.HTTPError):
        return error('Endpoint reported an error',
                     'The endpoint at ' + url + ' answered with HTTP ' + str(exc.code) + '.',
                     'Try again later or check the logs of the endpoint.')
    if isinstance(exc, SPARQLWrapperException):
        return error('Endpoint reported an error',
                     'The endpoint at ' + url + ' could not process the request.',
                     'Try again later or check the logs of the endpoint.')

    if isinstance(reason, ConnectionRefusedError) or isinstance(exc, ConnectionRefusedError):
        return error('Endpoint refused the connection',
                     'Nothing is accepting connections at ' + where + '.', reachability_hint)
    if isinstance(reason, socket.gaierror):
        return error('Endpoint host not found',
                     'The host name "' + host + '" could not be resolved.',
                     reachability_hint if (local or IN_DOCKER)
                     else 'Check the spelling of the host name and your network connection.')
    if isinstance(reason, ssl.SSLCertVerificationError):
        return error('Endpoint certificate rejected',
                     'The TLS certificate of ' + host + ' could not be verified.',
                     'Check that the certificate is valid and issued for this host name.')
    if isinstance(reason, ssl.SSLError):
        wrong_protocol = 'WRONG_VERSION_NUMBER' in str(reason)
        return error('Endpoint TLS error',
                     'A secure connection to ' + where + ' could not be established.',
                     'The server probably does not speak HTTPS on this port. Try http:// instead of https://.'
                     if wrong_protocol else 'Check the TLS configuration of the endpoint.')
    if isinstance(exc, (socket.timeout, TimeoutError)) or isinstance(reason, (socket.timeout, TimeoutError)):
        if during_validation:
            timeout_hint = ('The endpoint may be overloaded. Try again with a smaller maximum number of instances '
                            'per query under Advanced options.')
        else:
            timeout_hint = ('It may be busy or still starting up. Wait a moment and try again. The time limit of '
                            'this check is ' + str(ENDPOINT_CHECK_TIMEOUT) + ' seconds and can be changed with the '
                            'environment variable ENDPOINT_CHECK_TIMEOUT.')
        return error('Endpoint timed out', 'The endpoint at ' + where + ' did not answer in time.', timeout_hint)
    if isinstance(exc, (ConnectionError, http.client.HTTPException)):
        return error('Connection to the endpoint interrupted',
                     'The connection to ' + where + ' was closed unexpectedly.',
                     'The endpoint may have crashed or may be overloaded. Check its logs and try again.')
    return error('Endpoint not reachable',
                 'Trav-SHACL could not connect to ' + where + '.', reachability_hint)


# ---------------------------------------------------------------------------------------------------------------------
# errors during validation
# ---------------------------------------------------------------------------------------------------------------------

def explain_exception(exc, stage, schema_path, endpoint, upload_names=None):
    """
    Translates an unexpected exception into a message for the user.

    :param exc: the exception
    :param stage: 'shapes' while the shape schema is read, 'validation' while the validation is running
    :param schema_path: the shape schema location
    :param endpoint: the URL of the SPARQL endpoint
    :param upload_names: maps stored to original file names, if the shapes were uploaded instead of read from a location
    """
    if isinstance(exc, UserFacingError):
        return exc
    details = exc.__class__.__name__ + ': ' + str(exc)

    if stage == 'shapes':
        if isinstance(exc, NotImplementedError):
            return UserFacingError(
                'Unsupported feature in the shape schema',
                'The shapes use a SHACL feature that Trav-SHACL does not support.',
                hint='Set "Unsupported constraints" to "Skip and continue" under Advanced options to ignore them '
                     '(a warning is logged), or remove them from the shapes.',
                field='schemaDir', details=details)
        culprit = find_unparsable_file(schema_path)
        if culprit is not None:
            file, parse_error = culprit
            name = upload_names.get(os.path.basename(file), os.path.basename(file)) if upload_names \
                else os.path.relpath(file, schema_path)
            return UserFacingError(
                'Shape file could not be read',
                'The file ' + name + ' is not valid Turtle: ' + _summarize_parse_error(parse_error) + '.',
                hint='Fix the syntax error in the file and try again.',
                field='shapesFile' if upload_names else 'schemaDir',
                details=(name if upload_names else file) + '\n' + details)
        return UserFacingError('Shape schema could not be read',
                               'The shapes in "' + schema_path + '" could not be processed.',
                               hint='Check that the shapes are valid SHACL in Turtle syntax.',
                               field='schemaDir', details=details)

    if is_endpoint_error(exc):
        return explain_endpoint_error(exc, endpoint, during_validation=True)
    return UserFacingError('Unexpected error',
                           'The validation failed with ' + exc.__class__.__name__ + ': ' + str(exc),
                           hint='See the log of Trav-SHACL for the full stack trace.',
                           status=500, details=details)
