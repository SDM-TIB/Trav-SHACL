# -*- coding: utf-8 -*-
from __future__ import annotations  # required for typing in older versions of Python

__author__ = 'Philipp D. Rohde and Monica Figuera'

from rdflib import Graph

from TravSHACL.core.GraphTraversal import GraphTraversal
from TravSHACL.core.ShapeParser import ShapeParser
from TravSHACL.rule_based_validation.Validation import Validation
from TravSHACL.sparql.SPARQLEndpoint import SPARQLEndpoint
from TravSHACL.utils import parse_heuristics


class ShapeSchema:
    """This class represents a SHACL shape schema."""

    def __init__(self, *, schema_dir: str | Graph, schema_format: str = 'SHACL', endpoint: str | Graph,
                 endpoint_user: str = None, endpoint_password: str = None,
                 graph_traversal: GraphTraversal = GraphTraversal.DFS, heuristics: dict = parse_heuristics("TARGET IN BIG"),
                 use_selective_queries: bool = True, max_split_size: int = 256, output_dir: str = None,
                 order_by_in_queries: bool = False, save_outputs: bool = False, work_in_parallel: bool = False):
        """
        Creates a new shape schema instance.

        :param schema_dir: path of the files including the shape definitions (or an RDFlib graph)
        :param schema_format: indicates the format used for defining the shapes, this parameter should only
            be used if shapes defined in the legacy JSON format are used
        :param endpoint: URL for the SPARQL endpoint (or an RDFLib graph) to be evaluated against
        :param endpoint_user: username to connect to a private SPARQL endpoint; default: None
        :param endpoint_password: password to connect to a private SPARQL endpoint; default: None
        :param graph_traversal: graph traversal algorithm used for determining the evaluation order; default: DFS
        :param heuristics: Python dictionary holding the heuristics used for determining the seed shape;
            default is equivalent to `TARGET IN BIG`
        :param use_selective_queries: indicates whether selective queries are used; default: True
        :param max_split_size: maximum number of instances per query; default: 256
        :param output_dir: output directory for log files; default: None
        :param order_by_in_queries: indicates whether to use the ORDER BY clause; default: False
        :param save_outputs: indicates whether target classifications will be saved to the output path; default: False
        :param work_in_parallel: indicates whether parallelization will be used; not yet implemented; default: False
        """
        if isinstance(schema_dir, Graph):
            self.shapes = ShapeParser().parse_ttl(
                schema_dir, use_selective_queries, max_split_size, order_by_in_queries
            )
        else:
            self.shapes = ShapeParser().parse_shapes_from_dir(
                schema_dir, schema_format, use_selective_queries, max_split_size, order_by_in_queries
            )
        self.shapesDict = {shape.get_id(): shape for shape in self.shapes}  # TODO: use only the dict?
        self.endpoint = SPARQLEndpoint(endpoint, endpoint_user, endpoint_password)
        self.graphTraversal = graph_traversal
        self.parallel = work_in_parallel  # TODO: no parallelization implemented yet
        self.dependencies, self.reverse_dependencies = self.compute_edges()
        self.compute_in_and_outdegree()
        self.heuristics = heuristics
        self.outputDirName = output_dir
        self.selectivityEnabled = use_selective_queries
        self.saveStats = output_dir is not None
        self.saveTargetsToFile = save_outputs
        self.set_parent_shapes()

    def get_starting_point(self):
        """
        Use heuristics to determine the first shape for evaluation of the constraints.
        There might be several shapes that are equally suited, in this case all of them are returned.

        :return: list of possible starting points based on the heuristics
        """
        possible_starting_points = []

        # heuristic 1: target definition available
        if self.heuristics['target']:
            for s in self.shapes:
                if s.targetDef is not None:
                    possible_starting_points.append(s)

        # heuristic 2: in- and outdegree
        if self.heuristics['degree'] == 'in':
            # prioritize indegree
            possible_starting_points = possible_starting_points if possible_starting_points else self.shapes
            possible_starting_points = self.__indegree(possible_starting_points)
        elif self.heuristics['degree'] == 'out':
            # prioritize outdegree
            possible_starting_points = possible_starting_points if possible_starting_points else self.shapes
            possible_starting_points = self.__outdegree(possible_starting_points)
        elif self.heuristics['degree'] == 'inout':
            # prioritize indegree and further filter by outdegree
            possible_starting_points = possible_starting_points if possible_starting_points else self.shapes
            possible_starting_points = self.__indegree(possible_starting_points)
            possible_starting_points = self.__outdegree(possible_starting_points)
        elif self.heuristics['degree'] == 'outin':
            # prioritize outdegree and further filter by indegree
            possible_starting_points = possible_starting_points if possible_starting_points else self.shapes
            possible_starting_points = self.__outdegree(possible_starting_points)
            possible_starting_points = self.__indegree(possible_starting_points)

        # heuristic 3: number of properties
        if self.heuristics['properties'] == 'small':
            possible_starting_points = possible_starting_points if possible_starting_points else self.shapes
            if len(possible_starting_points) > 1:
                min_con = min([s.get_number_constraints() for s in possible_starting_points])
                tmp = []
                for s in possible_starting_points:
                    if s.get_number_constraints() == min_con:
                        tmp.append(s)
                possible_starting_points = tmp
        elif self.heuristics['properties'] == 'big':
            if len(possible_starting_points) > 1:
                max_con = max([s.get_number_constraints() for s in possible_starting_points])
                tmp = []
                for s in possible_starting_points:
                    if s.get_number_constraints() == max_con:
                        tmp.append(s)
                possible_starting_points = tmp

        if not possible_starting_points:
            possible_starting_points = all
        return [s.get_id() for s in possible_starting_points]

    @staticmethod
    def __indegree(possible_starting_points):
        if len(possible_starting_points) > 1:
            max_in = max([s.inDegree for s in possible_starting_points])
            tmp = []
            for s in possible_starting_points:
                if s.inDegree == max_in:
                    tmp.append(s)
            return tmp
        else:
            return possible_starting_points

    @staticmethod
    def __outdegree(possible_starting_points):
        if len(possible_starting_points) > 1:
            max_out = max([s.outDegree for s in possible_starting_points])
            tmp = []
            for s in possible_starting_points:
                if s.outDegree == max_out:
                    tmp.append(s)
            return tmp
        else:
            return possible_starting_points

    def set_parent_shapes(self):
        """Sets the shape referring to a shape as its parent."""
        for shape_name in self.shapesDict:
            child_shapes = self.shapesDict[shape_name].referencedShapes
            for child_name in child_shapes:
                self.shapesDict[child_name].add_parent_shape(shape_name)

    def validate(self):
        """Executes the validation of the shape network."""
        start = self.get_starting_point()
        node_order = self.graphTraversal.traverse_graph(self.dependencies, self.reverse_dependencies, start[0])  # TODO: deal with more than one possible starting point

        for s in self.shapes:
            s.compute_constraint_queries()

        target_shapes = [s for name, s in self.shapesDict.items()
                         if self.shapesDict[name].get_target_query() is not None]
        target_shape_predicates = [s.get_id() for s in target_shapes]

        return Validation(
            self.endpoint,
            node_order,
            self.shapesDict,
            target_shape_predicates,
            self.selectivityEnabled,
            self.outputDirName,
            self.saveStats,
            self.saveTargetsToFile
        ).exec()
        # return 'Go to log files in {} folder to see report'.format(self.outputDirName)

    def compute_in_and_outdegree(self):
        """Computes the in- and outdegree of each shape."""
        for s in self.shapes:
            s.set_degree(
                in_=len(self.reverse_dependencies[s.get_id()]) if s.get_id() in self.reverse_dependencies.keys() else 0,
                out_=len(self.dependencies[s.get_id()]) if s.get_id() in self.dependencies.keys() else 0
            )
        return

    def compute_edges(self):
        """Computes the edges in the network."""
        dependencies = {s.get_id(): [] for s in self.shapes}
        reverse_dependencies = {s.get_id(): [] for s in self.shapes}
        for s in self.shapes:
            refs = s.get_shape_refs()
            if refs:
                name = s.get_id()
                dependencies[name] = refs
                for ref in refs:
                    reverse_dependencies[ref].append(name)
        return dependencies, reverse_dependencies
