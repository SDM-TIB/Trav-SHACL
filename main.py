# -*- coding: utf-8 -*-
__author__ = "Philipp D. Rohde and Monica Figuera"

import argparse
import time

from travshacl.TravSHACL import eval_shape_schema

if __name__ == '__main__':
    """
    Used as a wrapper to start Trav-SHACL for evaluating a SHACL shape schema against a SPARQL endpoint.
    
    Example how to run it:
    python3 main.py -d ./shapes/nonRec/2/ "http://dbpedia.org/sparql" ./output/ DFS --heuristics TARGET IN BIG"""
    # add the optional flag '--selective' in the command line to use configuration of more selective queries
    # add the optional flag '--output' in the command line to store the target classifications as well

    start = time.time()

    parser = argparse.ArgumentParser(description='SHACL Constraint Validation over a SPARQL Endpoint')
    parser.add_argument('-d', metavar='schemaDir', type=str, default=None,
                        help='Directory containing shapes')
    parser.add_argument('endpoint', metavar='endpoint', type=str, default=None,
                        help='SPARQL Endpoint')
    parser.add_argument('outputDir', metavar='outputDir', type=str, default=None,
                        help='Name of the directory where results of validation will be saved')
    parser.add_argument(dest='graphTraversal', type=str, default='DFS', choices=['BFS', 'DFS'],
                        help='The algorithm used for graph traversal (BFS / DFS)')

    parser.add_argument("--heuristics", nargs="*", type=str, default=[],
                        help="TARGET if shapes with target definition should be prioritized\n"
                             "[IN / OUT / INOUT / OUTIN] if a higher in- or outdegree should be prioritized\n"
                             "[SMALL / BIG] if small or big shapes should be prioritized", required=True)

    parser.add_argument("--selective", action='store_true', default=False,
                        help="Use more selective queries", required=False)

    parser.add_argument("-m", metavar="maxSize", type=int, default=256,
                        help='max number of instances allowed to be in a query', required=False)

    parser.add_argument("--orderby", action='store_true', default=False,
                        help="Use ORDER BY keyword in queries", required=False)

    parser.add_argument("--outputs", action='store_true', default=False,
                        help="Save classified targets to output files", required=False)

    args = parser.parse_args()

    eval_shape_schema(args)

    end = time.time()
    print("Total program runtime:", end - start, "seconds")
