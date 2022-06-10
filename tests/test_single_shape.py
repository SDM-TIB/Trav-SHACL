import pytest
from . import run_test_case


@pytest.mark.parametrize("prio_number", ["BIG", "SMALL"])
@pytest.mark.parametrize("prio_degree", ["IN", "OUT"])
@pytest.mark.parametrize("prio_target", ["TARGET", ""])
@pytest.mark.parametrize("graph_traversal", ["DFS", "BFS"])
@pytest.mark.parametrize("selective", [True, False])
@pytest.mark.parametrize("order_by", [True, False])
def test_single_shape_one_min_constraint_one_property0(prio_number, prio_degree, prio_target, graph_traversal, selective, order_by):
    schema_dir = "./tests/constraints/single_shape/one_min_constraint/one_property0"
    ground_truth_file = "single_shape_one_min_constraint_one_property0"
    run_test_case(
        schema_dir=schema_dir,
        prio_number=prio_number,
        prio_degree=prio_degree,
        prio_target=prio_target,
        graph_traversal=graph_traversal,
        selective=selective,
        order_by=order_by,
        ground_truth_file=ground_truth_file
    )
