# -*- coding: utf-8 -*-
__author__ = "Philipp D. Rohde"

import os

from travshacl.core.GraphTraversal import GraphTraversal
from travshacl.core.ShapeSchema import ShapeSchema


def create_output_dir(output_dir):
    """
    Creates the output directory if it does not exist.

    :param output_dir: the output directory to be used
    """
    path = os.getcwd()
    os.makedirs(path + '/' + output_dir, exist_ok=True)


def parse_heuristics(input_):
    """
    Parses the heuristics from the arguments passed to Trav-SHACL.

    :param input_: the heuristics argument
    :return: Python dictionary with the heuristics to be used for the evaluation
    """
    heuristics = {}
    if 'TARGET' in input_:
        heuristics['target'] = True
    else:
        heuristics['target'] = False

    if 'IN' in input_:
        heuristics['degree'] = 'in'
    elif 'OUT' in input_:
        heuristics['degree'] = 'out'
    else:
        heuristics['degree'] = False

    if 'SMALL' in input_:
        heuristics['properties'] = 'small'
    elif 'BIG' in input_:
        heuristics['properties'] = 'big'
    else:
        heuristics['properties'] = False

    return heuristics


def eval_shape_schema(args):
    """
    Evaluates a SHACL shape schema against a SPARQL endpoint.

    :param args: command line arguments passed to Trav-SHACL
    """
    create_output_dir(args.outputDir)
    shape_schema = ShapeSchema(
        schema_dir=args.d,
        schema_format="JSON",
        endpoint_url=args.endpoint,
        graph_traversal=GraphTraversal.BFS if args.graphTraversal == "BFS" else GraphTraversal.DFS,
        heuristics=parse_heuristics(args.heuristics),
        use_selective_queries=args.selective,
        max_split_size=args.m,
        output_dir=args.outputDir,
        order_by_in_queries=args.orderby,
        save_outputs=args.outputs
    )

    report = shape_schema.validate()  # run the evaluation of the SHACL constraints over the specified endpoint
    print("Report:", report)
