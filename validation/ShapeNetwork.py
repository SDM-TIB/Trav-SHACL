# -*- coding: utf-8 -*-
__author__ = "Philipp D. Rohde and Monica Figuera"

from validation.core.ValidationTask import ValidationTask
from validation.ShapeParser import ShapeParser
from validation.sparql.SPARQLEndpoint import SPARQLEndpoint
from validation.utils.SourceDescription import SourceDescription
from validation.rule_based_validation.Validation import Validation

class ShapeNetwork:

    def __init__(self, schemaDir, schemaFormat, endpointURL, graphTraversal, validationTask, heuristics,
                 useSelectiveQueries, maxSplitSize, outputDir, ORDERBYinQueries, SHACL2SPARQLorder, saveOutputs,
                 workInParallel=False):
        self.sourceDescription = SourceDescription("./shapes/source-description.json")  # hardcoded for now
        self.shapes = ShapeParser().parseShapesFromDir(schemaDir, schemaFormat,
                                                       useSelectiveQueries, maxSplitSize, ORDERBYinQueries)
        self.shapesDict = {shape.getId(): shape for shape in self.shapes}  # TODO: use only the dict?
        self.endpointURL = endpointURL
        self.endpoint = SPARQLEndpoint(endpointURL)  # used in old_approach
        self.graphTraversal = graphTraversal
        self.validationTask = validationTask
        self.parallel = workInParallel
        self.dependencies, self.reverse_dependencies = self.computeEdges()
        self.computeInAndOutDegree()
        self.heuristics = heuristics
        self.outputDirName = outputDir
        self.selectivityEnabled = useSelectiveQueries
        self.useSHACL2SPARQLORDER = SHACL2SPARQLorder
        self.saveStats = outputDir is not None
        self.saveTargetsToFile = saveOutputs

    def getStartingPoint(self):
        """Use heuristics to determine the first shape for evaluation of the constraints."""
        # TODO: use parameters to allow customization of the heuristics used
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
            possible_starting_points = self._indegree(possible_starting_points)
        elif self.heuristics['degree'] == 'out':
            # priotizize outdegree
            possible_starting_points = possible_starting_points if possible_starting_points else self.shapes
            possible_starting_points = self._outdegree(possible_starting_points)
        elif self.heuristics['degree'] == 'inout':
            # prioritize indegree and further filter by outdegree
            possible_starting_points = possible_starting_points if possible_starting_points else self.shapes
            possible_starting_points = self._indegree(possible_starting_points)
            possible_starting_points = self._outdegree(possible_starting_points)
        elif self.heuristics['degree'] == 'outin':
            # prioritize outdegree and further filter by indegree
            possible_starting_points = possible_starting_points if possible_starting_points else self.shapes
            possible_starting_points = self._outdegree(possible_starting_points)
            possible_starting_points = self._indegree(possible_starting_points)

        # heuristic 3: number of properties
        if self.heuristics['properties'] == 'small':
            possible_starting_points = possible_starting_points if possible_starting_points else self.shapes
            if len(possible_starting_points) > 1:
                minCon = min([s.getNumberConstraints() for s in possible_starting_points])
                tmp = []
                for s in possible_starting_points:
                    if s.getNumberConstraints() == minCon:
                        tmp.append(s)
                possible_starting_points = tmp
        elif self.heuristics['properties'] == 'big':
            if len(possible_starting_points) > 1:
                maxCon = max([s.getNumberConstraints() for s in possible_starting_points])
                tmp = []
                for s in possible_starting_points:
                    if s.getNumberConstraints() == maxCon:
                        tmp.append(s)
                possible_starting_points = tmp

        if not possible_starting_points:
            possible_starting_points = all
        return [s.getId() for s in possible_starting_points]

    def _indegree(self, possible_starting_points):
        if len(possible_starting_points) > 1:
            maxIn = max([s.inDegree for s in possible_starting_points])
            tmp = []
            for s in possible_starting_points:
                if s.inDegree == maxIn:
                    tmp.append(s)
            return tmp
        else:
            return possible_starting_points

    def _outdegree(self, possible_starting_points):
        if len(possible_starting_points) > 1:
            maxOut = max([s.outDegree for s in possible_starting_points])
            tmp = []
            for s in possible_starting_points:
                if s.outDegree == maxOut:
                    tmp.append(s)
            return tmp
        else:
            return possible_starting_points

    def setParentShapes(self):
        for shape_name in self.shapesDict:
            child_shapes = self.shapesDict[shape_name].referencedShapes
            for child_name in child_shapes:
                self.shapesDict[child_name].addParentShape(shape_name)

    def validate(self):
        """Execute one of the validation tasks in validation.core.ValidationTask."""
        start = self.getStartingPoint()
        node_order = self.graphTraversal.traverse_graph(self.dependencies, self.reverse_dependencies, start[0])  # TODO: deal with more than one possible starting point
        self.setParentShapes()
        if self.validationTask == ValidationTask.GRAPH_VALIDATION:
            isSatisfied = self.isSatisfied(node_order)
            return isSatisfied
        elif self.validationTask == ValidationTask.SHAPE_VALIDATION:
            shapeReport = self.shapesSatisfiable(node_order)
            return shapeReport
        elif self.validationTask == ValidationTask.INSTANCES_VALID \
                or self.validationTask == ValidationTask.INSTANCES_VIOLATION \
                or self.validationTask == ValidationTask.ALL_INSTANCES:
            for s in self.shapes:
                s.computeConstraintQueries()

            option = "all"           # To report all instances
            if self.validationTask == ValidationTask.INSTANCES_VALID:
                option = "valid"     # To report only the instances that validate the constraints of the graph.
            elif self.validationTask == ValidationTask.INSTANCES_VIOLATION:
                option = "violated"  # To report only the instances that violate the constraints of the graph.

            instancesReport = self.getInstances(node_order, option)
            return instancesReport
        else:
            raise TypeError("Invalid validation task: " + self.validationTask)

    def computeInAndOutDegree(self):
        """Computes the in- and outdegree of each shape."""
        for s in self.shapes:
            s.outDegree = len(self.dependencies[s.getId()]) if s.getId() in self.dependencies.keys() else 0
            s.inDegree = len(self.reverse_dependencies[s.getId()]) if s.getId() in self.reverse_dependencies.keys() else 0
        return

    def computeEdges(self):
        """Computes the edges in the network."""
        dependencies = {s.getId(): [] for s in self.shapes}
        reverse_dependencies = {s.getId(): [] for s in self.shapes}
        for s in self.shapes:
            refs = s.getShapeRefs()
            if refs:
                name = s.getId()
                dependencies[name] = refs
                for ref in refs:
                    reverse_dependencies[ref].append(name)
        return dependencies, reverse_dependencies

    def isSatisfied(self, nodes):
        """Checks whether the graph is satisfiable or not."""
        for node in nodes:
            if not self.shapesDict[node].isSatisfied():
                return False
        return True

    def shapesSatisfiable(self, nodes):
        """Reports for each shape if it is satisfiable or not."""
        report = {}
        for node in nodes:
            report[node] = self.shapesDict[node].isSatisfied()
        return report

    def getInstances(self, node_order, option):
        """
        Reports valid and violated constraints of the graph
        :param node_order:
        :param option: has three possible values: 'all', 'valid', 'violated'
        """
        targetShapes = [s for name, s in self.shapesDict.items()
                        if self.shapesDict[name].getTargetQuery() is not None]
        targetShapePredicates = [s.getId() for s in targetShapes]

        Validation(
            self.endpointURL,
            node_order,
            self.shapesDict,
            option,
            targetShapePredicates,
            self.selectivityEnabled,
            self.useSHACL2SPARQLORDER,
            self.outputDirName,
            self.saveStats,
            self.saveTargetsToFile
        ).exec()
        return 'Go to log files in {} folder to see report'.format(self.outputDirName)
