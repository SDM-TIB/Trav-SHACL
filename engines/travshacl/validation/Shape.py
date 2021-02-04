# -*- coding: utf-8 -*-
__author__ = "Monica Figuera and Philipp D. Rohde"

import itertools
from validation.VariableGenerator import VariableGenerator
from validation.core.RulePattern import RulePattern
from validation.utils.SourceDescription import SourceDescription
from validation.sparql.QueryGenerator import QueryGenerator


class Shape:

    def __init__(self, id, targetDef, targetType, targetQuery, constraints, constraintsId, referencedShapes,
                 useSelectiveQueries, maxSplitSize, ORDERBYinQueries, includeSPARQLPrefixes):
        self.id = id
        self.constraints = constraints
        self.constraintsId = constraintsId
        self.predicates = []
        self.targetDef = targetDef
        self.targetType = targetType          # Might be None
        self.targetQuery = targetQuery        # Might be None
        self.targetQueryNoPref = targetQuery  # Might be None
        self.rulePatterns = ()
        self.satisfied = None
        self.inDegree = None
        self.outDegree = None

        self.minQuery = None
        self.maxQueries = None
        self.predicates = []

        self.referencedShapes = referencedShapes
        self.parentShapes = set()
        self.queriesWithVALUES = {}
        self.queriesWithFILTER_NOT_IN = {}  # complement of VALUES
        self.targets = {"valid": set(), "violated": set()}

        self.useSelectiveQueries = useSelectiveQueries
        self.maxSplitSize = maxSplitSize
        self.ORDERBYinQueries = ORDERBYinQueries
        self.includePrefixes = includeSPARQLPrefixes
        self.maxConstrId = {}
        self.queryGenerator = QueryGenerator()
        self.computeTargetQueries()

    def getId(self):
        return self.id

    def getPredicates(self):
        return self.predicates

    def setDegree(self, inDegree, outDegree):
        self.inDegree = inDegree
        self.outDegree = outDegree

    def computePredicateSet(self, minQueryId, maxQueriesIds):
        '''
        Returns the ids of the queries for a shape
        '''

        return [self.id] + [self.id + "_d1"] + [minQueryId] + [q for q in maxQueriesIds]

    def computeTargetDef(self):
        targets = SourceDescription.instance.get_classes(self.predicates)
        for c in self.constraints:
            c.target = targets
        # fix: set target for constraints only (needed for the queries)
        # but not for the shape since it will interfere with the heuristics
        return None

    def getTargetQuery(self):
        return self.targetQuery

    def getConstraints(self):
        return self.constraints

    def getNumberConstraints(self):
        """get the number of constraints belonging to this shape"""
        return len(self.constraints)

    def getShapeRefs(self):
        return [c.getShapeRef() for c in self.constraints if c.getShapeRef() is not None]

    def isSatisfied(self):
        if self.satisfied is None:
            for c in self.constraints:  # TODO: heuristics for the constraints within a shape?
                if not c.isSatisfied():
                    self.satisfied = False
                    return self.satisfied
            self.satisfied = True
        return self.satisfied

    def getRulePatterns(self):
        return self.rulePatterns

    def computeTargetQueries(self):
        self.targetQuery = self.queryGenerator.generate_target_query(
                                        "plain_target",
                                        None,
                                        self.targetQueryNoPref,
                                        self.includePrefixes,
                                        self.ORDERBYinQueries)

        self.queriesWithVALUES = {ref: self.queryGenerator.generate_target_query(
                                        "template_VALUES",
                                        [c for c in self.constraints if c.path == self.referencedShapes[ref]],
                                        self.targetQueryNoPref,
                                        self.includePrefixes,
                                        self.ORDERBYinQueries) for ref in self.referencedShapes.keys()}

        self.queriesWithFILTER_NOT_IN = {ref: self.queryGenerator.generate_target_query(
                                        "template_FILTER_NOT_IN",
                                        [c for c in self.constraints if c.path == self.referencedShapes[ref]],
                                        self.targetQueryNoPref,
                                        self.includePrefixes,
                                        self.ORDERBYinQueries) for ref in self.referencedShapes.keys()}

    def computeConstraintQueries(self):
        minConstraints = [c for c in self.constraints if c.min != -1]
        maxConstraints = [c for c in self.constraints if c.max != -1]

        subquery = self.queryGenerator.generate_local_subquery(minConstraints)

        # Build a unique set of triples (+ filter) for all min constraints
        minId = self.constraintsId + "_pos"
        self.minQuery = self.queryGenerator.generate_query(
                minId,
                [c for c in minConstraints if c.getShapeRef() is not None],
                self.useSelectiveQueries,
                self.targetQueryNoPref,
                self.includePrefixes,
                self.ORDERBYinQueries,
                subquery
        )

        # Build one set of triples (+ filter) for each max constraint (only one max constraint per query is allowed)
        maxIds = [self.constraintsId + "_max_" + str(i) for i in range(1, len(maxConstraints) + 1)]
        for i, max_c in enumerate(maxConstraints):
            self.maxConstrId[max_c] = self.constraintsId + "_max_" + str(i+1)

        i = itertools.count()
        self.maxQueries = {self.queryGenerator.generate_query(
                                        maxIds[next(i)],
                                        [c],
                                        self.useSelectiveQueries,
                                        self.targetQueryNoPref,
                                        self.includePrefixes,
                                        self.ORDERBYinQueries,
                                        subquery) for c in maxConstraints}

        self.predicates = self.computePredicateSet(minId, maxIds)
        self.rulePatterns = self.computeRulePatterns()

    def computeRulePatterns(self):
        """ Computes shape rule patterns """
        focusNodeVar = VariableGenerator.getFocusNodeVar()
        head = (self.id, focusNodeVar, True)

        return [RulePattern(head, self.getDisjunctRPBody())]

    def getDisjunctRPBody(self):
        focusNodeVar = VariableGenerator.getFocusNodeVar()
        maxQueries = [(s, focusNodeVar, False) for s in [q.getId() for q in self.maxQueries]]
        return [(self.minQuery.getId(),
                        focusNodeVar,
                        True
                        )] + \
                maxQueries

    def addParentShape(self, parentName):
        return self.parentShapes.add(parentName)

    def getParentShapes(self):
        return self.parentShapes

    def getValidTargets(self):
        return self.targets["valid"]

    def getInvalidTargets(self):
        return self.targets["violated"]

#    def getPosShapeRefs(self):
#        return [d.getPosShapeRefs() for d in self.disjuncts]

#    def getNegShapeRefs(self):
#        return [d.getNegShapeRefs() for d in self.disjuncts]

#    def askViolations(self):
#        if self.targetDef is not None:  # not checking violations on shapes without target definitions
#            triple = re.findall(r'{.*}', self.targetDef)[0]  # *** considering only one target def
#            triple = triple[1:len(triple)-1]  # removed curly braces
#            triple = triple.strip().split()
#            target = triple[2]
#
#            minConstraints = self.disjuncts[0].minConstraints
#            for c in minConstraints:
#                c.violated = ASKQuery(c.path, target).evaluate("min", c.min)
#
#            maxConstraints = self.disjuncts[0].maxConstraints
#            for c in maxConstraints:
#                c.violated = ASKQuery(c.path, target).evaluate("max", c.max)
