# -*- coding: utf-8 -*-
__author__ = "Philipp D. Rohde"

from validation.VariableGenerator import VariableType
from validation.constraints.Constraint import Constraint
from validation.sparql.ASKQuery import *


class MinMaxConstraint(Constraint):

    def __init__(self, varGenerator, id, path, min, max, isPos, datatype=None, value=None, shapeRef=None, targetDef=None):
        super().__init__(id, isPos, None, datatype, value, shapeRef, targetDef)
        self.varGenerator = varGenerator
        self.path = path
        self.min = min
        self.max = max
        self.variables = self.computeVariables()

    def computeVariables(self):
        atomicConstraint = Constraint()
        return atomicConstraint.generateVariables(self.varGenerator, VariableType.VALIDATION, self.min)

    @property
    def getMin(self):
        return self.min

    @property
    def getMax(self):
        return self.max

    @property
    def getPath(self):
        return self.path

    def isSatisfied(self):
        if self.satisfied is None:
            self.satisfied = not ASKQueryCardRangeConstraint(self.path, self.target, self.min, self.max, self.value).evaluate()

        return self.satisfied

    def getValidInstances(self):
        return []  # TODO

    def getViolations(self):
        return []  # TODO
