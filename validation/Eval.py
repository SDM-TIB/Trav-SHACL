# -*- coding: utf-8 -*-
import os
from validation.core.GraphTraversal import GraphTraversal
from validation.core.ValidationTask import ValidationTask
from validation.ShapeNetwork import ShapeNetwork


class Eval:
    def __init__(self, args):
        """
        :type args: ...
        """
        self.outputDir = args.outputDir
        self.shapeFormat = "JSON"

        self.task = None
        if args.g:
            self.task = ValidationTask.GRAPH_VALIDATION
        elif args.s:
            self.task = ValidationTask.SHAPE_VALIDATION
        elif args.t:
            self.task = ValidationTask.INSTANCES_VALID
        elif args.f:
            self.task = ValidationTask.INSTANCES_VIOLATION
        elif args.a:
            self.task = ValidationTask.ALL_INSTANCES

        if args.graphTraversal == "DFS":
            self.graphTraversal = GraphTraversal.DFS
        elif args.graphTraversal == "BFS":
            self.graphTraversal = GraphTraversal.BFS

        self.createOutputDir()
        schemaDir = args.d
        workInParallel = False
        useSelectiveQueries = args.selective
        maxSplitSize = args.m
        ORDERBYinQueries = args.orderby
        SHACL2SPARQLorder = args.s2s
        saveOutputs = args.outputs
        self.network = ShapeNetwork(schemaDir, self.shapeFormat, args.endpoint, self.graphTraversal, self.task,
                                    self.parseHeuristics(args.heuristics), useSelectiveQueries, maxSplitSize,
                                    self.outputDir, ORDERBYinQueries, SHACL2SPARQLorder, saveOutputs, workInParallel)

        report = self.network.validate()  # run the evaluation of the SHACL constraints over the specified endpoint
        print("Report:", report)

    def createOutputDir(self):
        path = os.getcwd()
        os.makedirs(path + '/' + self.outputDir, exist_ok=True)

    def parseHeuristics(self, input):
        heuristics = {}
        if 'TARGET' in input:
            heuristics['target'] = True
        else:
            heuristics['target'] = False

        if 'IN' in input:
            heuristics['degree'] = 'in'
        elif 'OUT' in input:
            heuristics['degree'] = 'out'
        else:
            heuristics['degree'] = False

        if 'SMALL' in input:
            heuristics['properties'] = 'small'
        elif 'BIG' in input:
            heuristics['properties'] = 'big'
        else:
            heuristics['properties'] = False

        return heuristics
