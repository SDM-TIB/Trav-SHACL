# -*- coding: utf-8 -*-
__author__ = "Philipp D. Rohde"

from validation.ShapeParser import ShapeParser
from validation.sparql.SPARQLEndpoint import SPARQLEndpoint
from validation.utils import fileManagement
from validation.RuleBasedValidation import RuleBasedValidation


class ShapeNetwork:

    def __init__(self, schemaDir, schemaFormat, endpointURL, useSelectiveQueries, maxSplitSize, outputDir, ORDERBYinQueries):
        self.shapes = ShapeParser().parseShapesFromDir(schemaDir, schemaFormat, useSelectiveQueries, maxSplitSize, ORDERBYinQueries)
        self.shapesDict = {shape.getId(): shape for shape in self.shapes}  # TODO: use only the dict?
        self.endpoint = SPARQLEndpoint(endpointURL)
        self.outputDirName = outputDir

    @staticmethod
    def get_node_order(shapes_count):
        """Hard-coded execution order based on the order SHACL2SPARQL uses."""
        if shapes_count == 3:
            return ['Department',
                    'University',
                    'FullProfessor']
        elif shapes_count == 7:
            return ['ResearchGroup',
                    'Department',
                    'University',
                    'Course',
                    'FullProfessor',
                    'UndergraduateStudent',
                    'Publication']
        elif shapes_count == 14:
            return ['ResearchGroup',
                    'ResearchAssistant',
                    'Department',
                    'University',
                    'Course',
                    'FullProfessor',
                    'AssociateProfessor',
                    'UndergraduateStudent',
                    'Lecturer',
                    'GraduateCourse',
                    'AssistantProfessor',
                    'Publication',
                    'GraduateStudent',
                    'TeachingAssistant']

    def validate(self):
        """Execute the Validation of the Shape Network."""
        node_order = self.get_node_order(len(self.shapes))

        for s in self.shapes:
            s.computeConstraintQueries()

        instancesReport = self.getInstances(node_order)
        return instancesReport

    def getInstances(self, node_order):
        """
        Reports valid and violated constraints of the graph
        :param node_order:
        :param option: has three possible values: 'all', 'valid', 'violated'
        """
        #print("Node order", node_order)
        RuleBasedValidation(
            self.endpoint,
            node_order,
            self.shapesDict,
            fileManagement.openFile(self.outputDirName, "validation.log"),
            fileManagement.openFile(self.outputDirName, "targets_valid.log"),
            fileManagement.openFile(self.outputDirName, "targets_violated.log"),
            fileManagement.openFile(self.outputDirName, "stats.txt"),
            fileManagement.openFile(self.outputDirName, "traces.csv")
        ).exec()
        return 'Go to log files in {} folder to see report'.format(self.outputDirName)
