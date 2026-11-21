import logging
import os
import time
from pathlib import Path

from flask import Flask, request, render_template
from werkzeug.middleware.proxy_fix import ProxyFix

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
app.config['VERSION_STRING'] = 'Trav-SHACL v' + __version__

# Defaults of the advanced options; they are identical to what the interface used before the options were exposed.
DEFAULT_OPTIONS = {
    'traversal': 'DFS',
    'target': 'yes',
    'degree': 'in',
    'properties': 'big',
    'selective': 'yes',
    'max_split_size': '256',
    'order_by': 'no'
}

logger = logging.getLogger(__name__)


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

    if not schema_path or not endpoint:
        return _render_form(schema_path, endpoint, options, error='Please provide both the shape schema path and the endpoint URL.'), 400

    try:
        config = _parse_options(options)
    except ValueError as e:
        return _render_form(schema_path, endpoint, options, error=str(e)), 400

    try:
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
            save_outputs=False
        )

        start = time.time()
        result = shape_schema.validate()
        stop = time.time()
    except Exception as e:
        logger.exception('Validation failed')
        message = str(e) or e.__class__.__name__
        return _render_form(schema_path, endpoint, options,
                            error='The validation could not be completed: ' + message), 500

    rows = travshacl_to_rows(result)
    counts = {
        'total': len(rows),
        'valid': sum(1 for r in rows if r['result'] == 'valid'),
        'invalid': sum(1 for r in rows if r['result'] == 'invalid')
    }
    return render_template('result.jinja2', title='Trav-SHACL - Validation Result',
                           rows=rows, counts=counts, elapsed=stop - start,
                           schema_path=schema_path, endpoint=endpoint, options=options)


def _render_form(schema_path, endpoint, options, error=None):
    return render_template('validate.jinja2', title='Trav-SHACL - Validate',
                           schema_path=schema_path, endpoint=endpoint, options=options, error=error,
                           options_changed=options != DEFAULT_OPTIONS)


def _parse_options(options):
    """Validates the advanced options of the form and translates them for ShapeSchema."""
    if options['traversal'] not in ('DFS', 'BFS'):
        raise ValueError('The graph traversal has to be either DFS or BFS.')
    if options['degree'] not in ('in', 'out', 'none'):
        raise ValueError('The degree heuristic has to be one of in, out, or none.')
    if options['properties'] not in ('big', 'small', 'none'):
        raise ValueError('The size heuristic has to be one of big, small, or none.')
    for key in ('target', 'selective', 'order_by'):
        if options[key] not in ('yes', 'no'):
            raise ValueError('Invalid value for the option "' + key + '".')
    try:
        max_split_size = int(options['max_split_size'])
    except ValueError:
        raise ValueError('The maximum number of instances per query has to be a whole number.') from None
    if max_split_size < 1:
        raise ValueError('The maximum number of instances per query has to be at least 1.')

    return {
        'traversal': GraphTraversal[options['traversal']],
        'heuristics': {
            'target': options['target'] == 'yes',
            'degree': False if options['degree'] == 'none' else options['degree'],
            'properties': False if options['properties'] == 'none' else options['properties']
        },
        'selective': options['selective'] == 'yes',
        'max_split_size': max_split_size,
        'order_by': options['order_by'] == 'yes'
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
