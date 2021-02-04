# -*- coding: utf-8 -*-
import os
from validation.ShapeNetwork import ShapeNetwork


class Eval:
    def __init__(self, args):
        """
        :type args: ...
        """
        self.outputDir = args.outputDir
        self.shapeFormat = "JSON"

        self.createOutputDir()
        schemaDir = args.d
        useSelectiveQueries = args.selective
        maxSplitSize = args.m
        ORDERBYinQueries = True
        self.network = ShapeNetwork(schemaDir, self.shapeFormat, args.endpoint, useSelectiveQueries,
                                    maxSplitSize, self.outputDir, ORDERBYinQueries)

        report = self.network.validate()  # run the evaluation of the SHACL constraints over the specified endpoint
        print("Report:", report)

    def createOutputDir(self):
        path = os.getcwd()
        os.makedirs(path + '/' + self.outputDir, exist_ok=True)
