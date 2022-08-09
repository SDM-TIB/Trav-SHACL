import json
from glob import glob

import pytest

from TravSHACL.TravSHACL import parse_heuristics
from TravSHACL.core.GraphTraversal import GraphTraversal
from TravSHACL.core.ShapeSchema import ShapeSchema

TEST_ENDPOINT = 'http://localhost:8899/sparql'


def get_all_test_cases():
    return glob('./tests/cases/**/definitions/*.json', recursive=True)


@pytest.mark.parametrize('file', get_all_test_cases())
@pytest.mark.parametrize('prio_number', ['BIG', 'SMALL'])
@pytest.mark.parametrize('prio_degree', ['IN', 'OUT'])
@pytest.mark.parametrize('prio_target', ['TARGET', ''])
@pytest.mark.parametrize('graph_traversal', ['DFS', 'BFS'])
@pytest.mark.parametrize('selective', [True, False])
def test_case(file, selective, graph_traversal, prio_target, prio_degree, prio_number):
    with open(file, 'r') as f:
        test_definition = json.load(f)

    schema_dir = test_definition['schemaDir']
    gt_valid = sorted(test_definition['groundTruth']['valid'])
    gt_invalid = sorted(test_definition['groundTruth']['invalid'])

    shape_schema = ShapeSchema(
        schema_dir=schema_dir,
        schema_format='JSON',
        endpoint_url=TEST_ENDPOINT,
        graph_traversal=GraphTraversal.BFS if graph_traversal == 'BFS' else GraphTraversal.DFS,
        heuristics=parse_heuristics(prio_target + ' ' + prio_degree + ' ' + prio_number),
        use_selective_queries=selective,
        max_split_size=256,
        output_dir=None,
        order_by_in_queries=False,
        save_outputs=False
    )
    result = shape_schema.validate()

    res_valid = []
    res_invalid = []

    for reason, value in result.items():
        for valres, instances in value.items():
            for instance in instances:
                if valres == 'valid_instances':
                    res_valid.append(instance[1])
                else:
                    res_invalid.append(instance[1])

    res_valid = sorted(res_valid)
    res_invalid = sorted(res_invalid)

    assert gt_valid == res_valid
    assert gt_invalid == res_invalid
