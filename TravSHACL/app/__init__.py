import os
import time

from flask import Flask, request, render_template

from TravSHACL.core.GraphTraversal import GraphTraversal
from TravSHACL.core.ShapeSchema import ShapeSchema

app = Flask(__name__)
app.config['SCHEMA_PATH'] = os.environ.get('SCHEMA_PATH', '/path/to/your/shacl')
app.config['ENDPOINT'] = os.environ.get('ENDPOINT', 'https://example.org/sparql')

HEURISTICS = {
    'target': True,
    'degree': 'in',
    'properties': 'big'
}

@app.route('/validate', methods=['GET', 'POST'])
def validation():
    if request.method == 'GET':
        return render_template('validate.html', schema_path=app.config['SCHEMA_PATH'], endpoint=app.config['ENDPOINT'])
    schema_path = request.form.get('schemaDir', None)
    endpoint = request.form.get('external_endpoint', None)

    shape_schema = ShapeSchema(
        schema_dir=schema_path,
        schema_format='SHACL',
        endpoint_url=endpoint,
        graph_traversal=GraphTraversal.DFS,
        heuristics=HEURISTICS,
        use_selective_queries=True,
        max_split_size=256,
        output_dir=None,
        order_by_in_queries=False,
        save_outputs=False
    )

    start = time.time()
    result = shape_schema.validate()
    stop = time.time()
    result_html = travshacl_to_html_table(result, stop - start)
    return render_template("result.html", html=result_html)

def travshacl_to_html_table(trav_result, time_used):
    parsed_result = []

    for shape, validation_dict in trav_result.items():
        for validation_result, instances in validation_dict.items():
            for instance in instances:
                finished_at = shape
                if finished_at[0] == '<':
                    finished_at = finished_at[1:]
                if finished_at[-1] == '>':
                    finished_at = finished_at[:-1]

                shape_ = instance[0]
                if shape_[0] == '<':
                    shape_ = shape_[1:]
                if shape_[-1] == '>':
                    shape_ = shape_[:-1]
                parsed_result.append({'shape': shape_, 'finished@shape': finished_at, 'validation result': validation_result.replace('_instances',''), 'instance': instance[1]})

    html = '<div>Trav-SHACL returned ' + str(len(parsed_result)) + ' validation results in ' + str(time_used) + ' seconds.<br><br><table border="0px" style="border-spacing: 10px; margin-left: auto; margin-right: auto;">'

    order = []
    html += '<tr>'
    for item in ['instance', 'shape', 'validation result', 'finished@shape']:
        order.append(item)
        html += '<th>' + item + '</th>'
    html += '</tr>'

    for res in parsed_result:
        html += '<tr>'
        for item in order:
            if res[item]:
                if item == 'validation result':
                    if res[item] == 'valid':
                        html += '<td style="color: green">' + str(res[item]) + '</td>'
                    else:
                        html += '<td style="color: red">' + str(res[item]) + '</td>'
                else:
                    html += '<td>' + str(res[item]) + '</td>'
        html += '</tr>'

    html += '</table></div>'
    return html

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)