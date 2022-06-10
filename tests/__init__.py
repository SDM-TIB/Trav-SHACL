import json

from travshacl.TravSHACL import parse_heuristics
from travshacl.core.GraphTraversal import GraphTraversal
from travshacl.core.ShapeSchema import ShapeSchema

TEST_ENDPOINT = "http://localhost:8899/sparql"


def execute_validation(schema_dir, prio_number, prio_degree, prio_target, graph_traversal, selective, order_by):
    shape_schema = ShapeSchema(
        schema_dir=schema_dir,
        schema_format="JSON",
        endpoint_url=TEST_ENDPOINT,
        graph_traversal=GraphTraversal.BFS if graph_traversal == "BFS" else GraphTraversal.DFS,
        heuristics=parse_heuristics(prio_target + " " + prio_degree + " " + prio_number),
        use_selective_queries=selective,
        max_split_size=256,
        output_dir=None,
        order_by_in_queries=order_by,
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

    return sorted(valid_results), sorted(invalid_results)


def get_ground_truth(file_name):
    file = open("./tests/ground_truth/" + file_name + ".json")
    ground_truth = json.load(file)
    file.close()
    return sorted(ground_truth["valid"]), sorted(ground_truth["invalid"])


def run_test_case(schema_dir, prio_number, prio_degree, prio_target, graph_traversal, selective, order_by, ground_truth_file):
    res_valid, res_invalid = execute_validation(schema_dir, prio_number, prio_degree, prio_target, graph_traversal, selective, order_by)
    gt_valid, gt_invalid = get_ground_truth(ground_truth_file)

    assert gt_valid == res_valid
    assert gt_invalid == res_invalid
