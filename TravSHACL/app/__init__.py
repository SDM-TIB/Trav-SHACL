import os
import shutil
import tempfile
import time
from pathlib import Path

from flask import Flask, request, render_template
from werkzeug.middleware.proxy_fix import ProxyFix

from TravSHACL.app.diagnostics import UserFacingError, check_endpoint, check_schema_dir, explain_exception, \
    save_uploaded_shapes
from TravSHACL.core.GraphTraversal import GraphTraversal
from TravSHACL.core.ShapeSchema import ShapeSchema
from TravSHACL.sparql.SPARQLEndpoint import SPARQLEndpoint


def _read_version() -> str:
    """Reads the version from the VERSION file in the root of the repository."""
    try:
        return (Path(__file__).resolve().parents[2] / 'VERSION').read_text(encoding='utf-8').strip()
    except OSError:
        return 'unknown'


__version__ = _read_version()


class _TravSHACLApp(Flask):
    def select_jinja_autoescape(self, filename):
        # By default, Flask only escapes *.html, *.htm, *.xml, *.xhtml, and *.svg templates.
        # Our templates end in *.jinja2; their values (IRIs, paths, error messages) have to be escaped, too.
        return True


app = _TravSHACLApp(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_prefix=1)  # support running behind a reverse proxy with a path prefix
app.config['SCHEMA_PATH'] = os.environ.get('SCHEMA_PATH', '/path/to/your/shacl')
app.config['ENDPOINT'] = os.environ.get('ENDPOINT', 'https://example.org/sparql')
app.config['VERSION'] = __version__
# Upper limit for the size of an uploaded shapes file (in MiB); larger requests are rejected with HTTP 413.
app.config['MAX_CONTENT_LENGTH'] = int(os.environ.get('MAX_UPLOAD_SIZE_MB', '10')) * 1024 * 1024
app.config['VERSION_STRING'] = 'Trav-SHACL v' + __version__

# Defaults of the advanced options; they are identical to what the interface used before the options were exposed.
DEFAULT_OPTIONS = {
    'traversal': 'DFS',
    'target': 'yes',
    'degree': 'in',
    'properties': 'big',
    'selective': 'yes',
    'max_split_size': '256',
    'order_by': 'no',
    'ignore_errors': 'no'
}


@app.errorhandler(413)
def upload_too_large(_):
    limit = app.config['MAX_CONTENT_LENGTH'] // (1024 * 1024)
    error = UserFacingError('Shapes file too large', 'The uploaded file exceeds the limit of ' + str(limit) + ' MiB.',
                            hint='Split the shapes or raise the limit with the environment variable MAX_UPLOAD_SIZE_MB.',
                            field='shapesFile', status=413)
    return _render_form('', app.config['ENDPOINT'], dict(DEFAULT_OPTIONS), error=error), 413


@app.context_processor
def inject_version():
    return {'version_string': app.config['VERSION_STRING']}


@app.route('/', methods=['GET'])
def home():
    return render_template('home.jinja2', title='Trav-SHACL - Home')


@app.route('/validate', methods=['GET', 'POST'])
def validation():
    if request.method == 'GET':
        return _render_form(app.config['SCHEMA_PATH'], app.config['ENDPOINT'], dict(DEFAULT_OPTIONS))

    # Fields that are absent (e.g., when the form is posted by a script) fall back to their defaults.
    schema_path = (request.form.get('schemaDir') or '').strip()
    endpoint = (request.form.get('external_endpoint') or '').strip()
    options = {key: request.form.get(key, default) for key, default in DEFAULT_OPTIONS.items()}
    shapes_file = request.files.get('shapesFile')
    uploaded = shapes_file is not None and bool(shapes_file.filename)

    # An uploaded file takes precedence over the location. It is copied into a temporary directory that only exists
    # for the duration of the request and is removed afterwards, no matter whether the validation succeeded.
    temp_dir = tempfile.mkdtemp(prefix='travshacl-') if uploaded else None
    stage = 'shapes'  # tells where an unexpected exception came from
    try:
        if uploaded:
            schema_path = save_uploaded_shapes(shapes_file, temp_dir)
        config = _parse_options(options)
        # Fail fast with a helpful message instead of running into an obscure error later on.
        check_schema_dir(schema_path)
        endpoint_has_data = check_endpoint(endpoint)

        SPARQLEndpoint.instance = None  # Needs to be reset since it is a singleton and won't change otherwise
        shape_schema = ShapeSchema(
            schema_dir=schema_path,
            schema_format='SHACL',
            endpoint=endpoint,
            graph_traversal=config['traversal'],
            heuristics=config['heuristics'],
            use_selective_queries=config['selective'],
            max_split_size=config['max_split_size'],
            output_dir=None,
            order_by_in_queries=config['order_by'],
            save_outputs=False,
            ignore_parsing_errors=config['ignore_errors']
        )

        stage = 'validation'
        start = time.time()
        result = shape_schema.validate()
        stop = time.time()
    except Exception as e:
        # The temporary directory is still needed here since explaining the error may parse the shape files again.
        error = explain_exception(e, stage, schema_path, endpoint, upload_name=shapes_file.filename if uploaded else None)
        if error.status == 500:  # unexpected; everything else is explained to the user and needs no stack trace
            app.logger.exception('Validation failed')
        else:
            app.logger.warning('%s: %s', error.title, error.details or error.message)
        form_path = '' if uploaded else schema_path  # never show the (deleted) temporary path
        return _render_form(form_path, endpoint, options, error=error), error.status
    finally:
        if temp_dir is not None:
            shutil.rmtree(temp_dir, ignore_errors=True)

    if uploaded:
        schema_path = 'uploaded file: ' + os.path.basename(shapes_file.filename)

    rows = travshacl_to_rows(result)
    counts = {
        'total': len(rows),
        'valid': sum(1 for r in rows if r['result'] == 'valid'),
        'invalid': sum(1 for r in rows if r['result'] == 'invalid')
    }
    notices = []
    if counts['total'] == 0:
        # Name the likely causes of an empty result.
        if not endpoint_has_data:
            notices.append('The endpoint is reachable, but it returned no triples. '
                           'Check that the data is loaded and that the endpoint URL points to the right dataset.')
        if not any(shape.targetDef is not None for shape in shape_schema.shapes):
            notices.append('None of the shapes defines a target, for example with sh:targetClass. '
                           'Without targets, there are no entities to validate.')
    return render_template('result.jinja2', title='Trav-SHACL - Validation Result',
                           rows=rows, counts=counts, elapsed=stop - start, notices=notices,
                           schema_path=schema_path, endpoint=endpoint, options=options)


def _render_form(schema_path, endpoint, options, error=None):
    return render_template('validate.jinja2', title='Trav-SHACL - Validate',
                           schema_path=schema_path, endpoint=endpoint, options=options, error=error,
                           options_changed=options != DEFAULT_OPTIONS)


def _invalid_option(message):
    return UserFacingError('Invalid option', message)


def _parse_options(options):
    """Validates the advanced options of the form and translates them for ShapeSchema."""
    if options['traversal'] not in ('DFS', 'BFS'):
        raise _invalid_option('The graph traversal has to be either DFS or BFS.')
    if options['degree'] not in ('in', 'out', 'none'):
        raise _invalid_option('The degree heuristic has to be one of in, out, or none.')
    if options['properties'] not in ('big', 'small', 'none'):
        raise _invalid_option('The size heuristic has to be one of big, small, or none.')
    for key in ('target', 'selective', 'order_by', 'ignore_errors'):
        if options[key] not in ('yes', 'no'):
            raise _invalid_option('Invalid value for the option "' + key + '".')
    try:
        max_split_size = int(options['max_split_size'])
    except ValueError:
        raise _invalid_option('The maximum number of instances per query has to be a whole number.') from None
    if max_split_size < 1:
        raise _invalid_option('The maximum number of instances per query has to be at least 1.')

    return {
        'traversal': GraphTraversal[options['traversal']],
        'heuristics': {
            'target': options['target'] == 'yes',
            'degree': False if options['degree'] == 'none' else options['degree'],
            'properties': False if options['properties'] == 'none' else options['properties']
        },
        'selective': options['selective'] == 'yes',
        'max_split_size': max_split_size,
        'order_by': options['order_by'] == 'yes',
        'ignore_errors': options['ignore_errors'] == 'yes'
    }


def _strip_brackets(iri: str) -> str:
    if iri.startswith('<'):
        iri = iri[1:]
    if iri.endswith('>'):
        iri = iri[:-1]
    return iri


def travshacl_to_rows(trav_result) -> list:
    """
    Flattens the result of Trav-SHACL into a list of table rows.

    Escaping is left to Jinja2; no HTML is generated here.
    """
    rows = []
    for finished_at, validation_dict in trav_result.items():
        for validation_result, instances in validation_dict.items():
            for target in instances:
                # a target is a tuple of at least (shape, instance); further elements are internal and not shown
                rows.append({
                    'instance': str(target[1]),
                    'shape': _strip_brackets(target[0]),
                    'result': validation_result.replace('_instances', ''),
                    'finished_at': _strip_brackets(finished_at)
                })
    return rows


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
