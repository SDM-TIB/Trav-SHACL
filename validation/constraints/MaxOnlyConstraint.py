# -*- coding: utf-8 -*-
__author__ = "Monica Figuera and Philipp D. Rohde"

from validation.VariableGenerator import VariableType
from validation.constraints.Constraint import Constraint
from validation.sparql.ASKQuery import *


class MaxOnlyConstraint(Constraint):

    def __init__(self, varGenerator, id, path, max, isPos, datatype=None, value=None, shapeRef=None, targetDef=None):
        super().__init__(id, isPos, None, datatype, value, shapeRef, targetDef)
        self.varGenerator = varGenerator
        self.path = path
        self.min = -1
        self.max = max
        self.variables = self.computeVariables()

    def computeVariables(self):
        atomicConstraint = Constraint()
        return atomicConstraint.generateVariables(self.varGenerator, VariableType.VALIDATION, self.max + 1)

    @property
    def getMax(self):
        return self.max

    @property
    def getPath(self):
        return self.path

    def isSatisfied(self):
        if self.satisfied is None:
            self.satisfied = not ASKQueryMaxCardConstraint(self.path, self.target, self.max, self.value).evaluate()

        return self.satisfied

    def getValidInstances(self):
        return []  # TODO

    def getViolations(self):
        return []  # TODO
