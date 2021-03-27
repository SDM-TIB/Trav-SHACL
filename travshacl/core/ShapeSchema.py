# -*- coding: utf-8 -*-
__author__ = "Philipp D. Rohde and Monica Figuera"

from travshacl.core.ShapeParser import ShapeParser
from travshacl.rule_based_validation.Validation import Validation


class ShapeSchema:
    """This class represents a SHACL shape schema."""

    def __init__(self, schema_dir, schema_format, endpoint_url, graph_traversal, heuristics, use_selective_queries,
                 max_split_size, output_dir, order_by_in_queries, save_outputs, work_in_parallel=False):
        """
        Creates a new shape schema instance.

        :param schema_dir: path of the files including the shape definitions
        :param schema_format: indicates the format used for defining the shapes
        :param endpoint_url: URL for the SPARQL endpoint to be evaluated against
        :param graph_traversal: graph traversal algorithm used for determining the evaluation order
        :param heuristics: Python dictionary holding the heuristics used for determining the seed shape
        :param use_selective_queries: indicates whether or not selective queries are used
        :param max_split_size: maximum number of instances per query
        :param output_dir: output directory for log files
        :param order_by_in_queries: indicates whether or not to use the ORDER BY clause
        :param save_outputs: indicates whether or not target classifications will be saved to the output path
        :param work_in_parallel: indicates whether or not parallelization will be used
        """
        self.shapes = ShapeParser().parse_shapes_from_dir(schema_dir, schema_format, use_selective_queries,
                                                          max_split_size, order_by_in_queries)
        self.shapesDict = {shape.get_id(): shape for shape in self.shapes}  # TODO: use only the dict?
        self.endpointURL = endpoint_url
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
            # priotizize outdegree
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

        Validation(
            self.endpointURL,
            node_order,
            self.shapesDict,
            target_shape_predicates,
            self.selectivityEnabled,
            self.outputDirName,
            self.saveStats,
            self.saveTargetsToFile
        ).exec()
        return 'Go to log files in {} folder to see report'.format(self.outputDirName)

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
