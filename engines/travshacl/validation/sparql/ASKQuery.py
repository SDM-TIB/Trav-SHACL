# -*- coding: utf-8 -*-
__author__ = "Monica Figuera and Philipp D. Rohde"

import re
from validation.sparql.SPARQLEndpoint import SPARQLEndpoint
from validation.sparql.SPARQLPrefixHandler import getPrefixString
# TODO: Use RDF-MTs for calculating class of shapes without target definition


class ASKQuery:
    def __init__(self, constraint, target, value):
        self.constraint = constraint
        self.target = target
        self.value = value

    def getQuery(self):
        query = "ASK {\n"

        inverse_path = self.constraint.startswith("^")
        subj = "?s" if not inverse_path else "?o"
        pred = self.constraint if not inverse_path else self.constraint[1:]
        if not inverse_path:
            obj = "?o" if self.value is None else self.value
        else:
            obj = "?s" if self.value is None else self.value

        if self.target is not None:
            if not isinstance(self.target, list):
                query += "\t%s a %s\n" % (subj, self.target)
            elif self.target:  # list and not empty
                query += "\t%s a ?type .\n" % subj
                query += "\tFILTER ("
                for i, type in enumerate(self.target):
                    if i != 0:
                        query += " OR "
                    query += "?type = <%s>" % type
                query += ")\n"

        if isinstance(self, ASKQueryCardConstraint):
            if isinstance(self, ASKQueryMinCardConstraint) and self.cardinality == 1:  # exists constraint
                query += "\tFILTER NOT EXISTS {\n\t\t%s %s %s\n\t}" % (subj, pred, obj)
            else:  # real cardinality constraint
                query += "\t{\n\t\tSELECT %s COUNT(%s) AS ?cnt WHERE {\n\t\t\t%s %s %s\n\t\t} GROUP BY %s\n\t}\n" % (subj, obj, subj, pred, obj, subj)
                if isinstance(self, ASKQueryMinCardConstraint):
                    query += "\tFILTER( ?cnt < %s )" % str(self.cardinality)
                elif isinstance(self, ASKQueryMaxCardConstraint):
                    query += "\tFILTER( ?cnt > %s )" % str(self.cardinality)
                elif isinstance(self, ASKQueryCardRangeConstraint):
                    query += "\tFILTER( ?cnt < %s OR ?cnt > %s)" % (str(self.min), str(self.max))
        else:
            raise TypeError("Unsupported ASK query type: " + str(self.__class__))

        query += "\n}"
        return query

    def evaluate(self):
        results = SPARQLEndpoint.instance.runQuery(None, getPrefixString() + self.getQuery())  # TODO: generate ID for the query?
        if re.search("true", results.toxml()):
            return True
        else:
            return False


class ASKQueryCardConstraint(ASKQuery):
    def __init__(self, constraint, target, type, cardinality, value=None):
        super().__init__(constraint, target, value)
        self.type = type
        self.cardinality = cardinality


class ASKQueryMinCardConstraint(ASKQueryCardConstraint):
    def __init__(self, constraint, target, cardinality, value):
        super().__init__(constraint, target, "min", cardinality, value)


class ASKQueryMaxCardConstraint(ASKQueryCardConstraint):
    def __init__(self, constraint, target, cardinality, value):
        super().__init__(constraint, target, "max", cardinality, value)


class ASKQueryCardRangeConstraint(ASKQueryCardConstraint):
    def __init__(self, constraint, target, min, max, value):
        super().__init__(constraint, target, "in", [min, max], value)
        self.min = min
        self.max = max
