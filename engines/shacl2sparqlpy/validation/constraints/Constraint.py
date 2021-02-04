# -*- coding: utf-8 -*-
__author__ = "Monica Figuera and Philipp D. Rohde"

from validation.core.Literal import Literal


class Constraint:

    def __init__(self, id=None, isPos=None, satisfied=None, datatype=None, value=None, shapeRef=None, targetDef=None):
        self.id = id
        self.isPos = isPos
        self.satisfied = satisfied

        self.datatype = datatype
        self.value = value
        self.shapeRef = shapeRef
        self.target = targetDef

        self.variables = []

    def getDatatype(self):
        return self.datatype

    def getValue(self):
        return self.value

    def getShapeRef(self):
        return self.shapeRef

    def getTarget(self):
        return self.target

    def getId(self):
        return self.id

    def getIsPos(self):
        return self.isPos

    def generateVariables(self, varGenerator, type, numberOfVariables):
        vars = []
        for elem in range(numberOfVariables):
            vars.append(varGenerator.generateVariable(type))

        return vars

    def getVariables(self):
        return self.variables

    def computeRulePatternBody(self):
        return [Literal(self.shapeRef, v, self.isPos) for v in self.variables] \
                    if self.shapeRef is not None else []
