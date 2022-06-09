import pytest
from . import TEST_ENDPOINT
from travshacl.core.GraphTraversal import GraphTraversal
from travshacl.core.ShapeSchema import ShapeSchema
from travshacl.TravSHACL import parse_heuristics


@pytest.mark.parametrize("graph_traversal", ['DFS', 'BFS'])
@pytest.mark.parametrize("selective", [True, False])
def test_single_shape_one_min_constraint_one_property0(graph_traversal, selective):
    graph_traversal = GraphTraversal.BFS if graph_traversal == "BFS" else GraphTraversal.DFS

    shape_schema = ShapeSchema(
        schema_dir="./tests/constraints/single_shape/one_min_constraint/one_property0",
        schema_format="JSON",
        endpoint_url=TEST_ENDPOINT,
        graph_traversal=graph_traversal,
        heuristics=parse_heuristics("TARGET IN BIG"),
        use_selective_queries=selective,
        max_split_size=256,
        output_dir=None,
        order_by_in_queries=True,
        save_outputs=False
    )
    result = shape_schema.validate()

    valid_results = []
    invalid_results = []

    for reason, value in result.items():
        for valres, instances in value.items():
            for instance in instances:
                if valres == "valid_instances":
                    valid_results.append(instance[1])
                else:
                    invalid_results.append(instance[1])

    valid_results = sorted(valid_results)
    invalid_results = sorted(invalid_results)

    gt_valid = sorted(["http://test.example.com/ClassA_Instance0", "http://test.example.com/ClassA_Instance1"])
    gt_invalid = sorted(["http://test.example.com/ClassA_Instance2"])

    assert gt_valid == valid_results
    assert gt_invalid == invalid_results
