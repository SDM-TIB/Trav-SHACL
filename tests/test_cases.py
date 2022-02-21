import pytest
from glob import glob
from argparse import Namespace
import json, os
from travshacl.core.GraphTraversal import GraphTraversal
from travshacl.core.ShapeSchema import ShapeSchema
from travshacl.TravSHACL import parse_heuristics

TEST_ENDPOINT='http://0.0.0.0:14000/sparql'
OUTPUT_DIR='tests/output/'
TEST_CASES_DIR='tests/cases/'

DEFAULT_PARAMS={
    "task":"a",
    "traversalStrategie":"DFS",
    "heuristic": "TARGET IN BIG",
    "targetShape": None,
    "maxSplit": 256,
    "selective": True,
    "orderBy": False
}

def get_all_test_cases():
    return glob(TEST_CASES_DIR + '**/definitions/*.json', recursive=True)

@pytest.mark.parametrize("file", get_all_test_cases())
@pytest.mark.parametrize("prio_number", ['BIG','SMALL'])
@pytest.mark.parametrize("prio_degree", ['IN','OUT'])
@pytest.mark.parametrize("prio_target", ['TARGET',''])
@pytest.mark.parametrize("graphTraversal", ['DFS','BFS'])
@pytest.mark.parametrize("selective", [True, False])
def test_case(file,selective, graphTraversal, prio_target, prio_degree, prio_number):
    with open(file, 'r') as f:
        test_case = json.load(f)

    target_shape = test_case['targetShape']
    use_selective_queries = selective if selective != None else test_case.get('selective', DEFAULT_PARAMS['selective'])
    graphTraversal = graphTraversal if graphTraversal != None else test_case.get('traversalStrategie', DEFAULT_PARAMS['traversalStrategie'])
    graph_traversal = GraphTraversal.BFS if graphTraversal == 'BFS' else GraphTraversal.DFS

    if prio_target != None and prio_degree != None and prio_number != None:
        heursitics_str = prio_target + ' ' + prio_degree + ' ' + prio_number
    else:
        heursitics_str = test_case.get('heuristic', DEFAULT_PARAMS['heuristic'])

    shape_schema = ShapeSchema(
        schema_dir=os.path.realpath(test_case['schemaDir']),
        schema_format="JSON",
        endpoint_url=TEST_ENDPOINT,
        graph_traversal=graph_traversal,
        heuristics=parse_heuristics(heursitics_str),
        use_selective_queries=use_selective_queries,
        max_split_size=test_case.get('maxSplit', DEFAULT_PARAMS['maxSplit']),
        output_dir=OUTPUT_DIR,
        order_by_in_queries=test_case.get('orderBy', DEFAULT_PARAMS['orderBy']),
        save_outputs=True
    )
    result = shape_schema.validate()

    valid_results = []
    invalid_results = []

    for reason, value in result.items():
        for valres, instances in value.items(): 
            for instance in instances:
                if instance[0] == target_shape:
                    if valres == 'valid_instances':
                        valid_results.append(instance[1])
                    else:
                        invalid_results.append(instance[1])


    gt_valids = sorted([item[0] for item in test_case['result']['validTargets']])
    gt_invalids = sorted([item[0] for item in test_case['result']['invalidTargets']])


    valid_results = sorted(valid_results)
    invalid_results = sorted(invalid_results)

    assert gt_valids == valid_results
    assert gt_invalids == invalid_results




