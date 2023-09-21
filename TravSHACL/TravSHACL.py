# -*- coding: utf-8 -*-
__author__ = 'Philipp D. Rohde'

from TravSHACL.core.GraphTraversal import GraphTraversal
from TravSHACL.core.ShapeSchema import ShapeSchema
from TravSHACL.utils import parse_heuristics


def eval_shape_schema(args):
    """
    Evaluates a SHACL shape schema against a SPARQL endpoint.

    :param args: command line arguments passed to Trav-SHACL
    """
    shape_schema = ShapeSchema(
        schema_dir=args.d,
        schema_format='JSON' if args.json else 'SHACL',
        endpoint=args.endpoint,
        graph_traversal=GraphTraversal.BFS if args.graphTraversal == 'BFS' else GraphTraversal.DFS,
        heuristics=parse_heuristics(args.heuristics),
        use_selective_queries=args.selective,
        max_split_size=args.m,
        output_dir=args.outputDir,
        order_by_in_queries=args.orderby,
        save_outputs=args.outputs
    )

    report = shape_schema.validate()  # run the evaluation of the SHACL constraints over the specified endpoint
    if not args.outputs:
        print('Report:', report)
