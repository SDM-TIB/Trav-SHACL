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
        self.rulePattern = ()
        self.satisfied = None
        self.inDegree = None
        self.outDegree = None

        self.minQuery = None
        self.maxQueries = None
        self.predicates = []
        self.maxValidRefs = {}
        self.skippedQueriesIds = set()

        self.referencedShapes = referencedShapes
        self.parentShapes = set()
        self.queriesWithVALUES = {}
        self.queriesWithFILTER_NOT_IN = {}  # complement of VALUES
        self.targets = {"valid": set(), "violated": set()}

        self.useSelectiveQueries = useSelectiveQueries
        self.querySplitThreshold = maxSplitSize
        self.ORDERBYinQueries = ORDERBYinQueries
        self.includePrefixes = includeSPARQLPrefixes
        self.maxConstrId = {}

        self.QueryGenerator = QueryGenerator()
        self.__compute_target_queries()

    def get_id(self):
        return self.id

    def get_predicates(self):
        return self.predicates

    def setDegree(self, inDegree, outDegree):
        self.inDegree = inDegree
        self.outDegree = outDegree

    def computeTargetDef(self):
        targets = SourceDescription.instance.get_classes(self.predicates)
        for c in self.constraints:
            c.target = targets
        # fix: set target for constraints only (needed for the queries)
        # but not for the shape since it will interfere with the heuristics
        return None

    def __compute_predicate_set(self, min_query_id, max_queries_ids):
        """ Returns the ids of the queries for this shape """
        return [self.id] + [self.id + "_d1"] + [min_query_id] + [q for q in max_queries_ids]

    def get_target_query(self):
        return self.targetQuery

    def get_constraints(self):
        return self.constraints

    def getNumberConstraints(self):
        """ Gets the number of constraints belonging to this shape """
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

    def get_rule_pattern(self):
        return self.rulePattern

    def get_query_split_threshold(self):
        return self.querySplitThreshold

    def __compute_target_queries(self):
        self.targetQuery = self.QueryGenerator.generate_target_query(
                                        "plain_target",
                                        None,
                                        self.targetQueryNoPref,
                                        self.includePrefixes,
                                        self.ORDERBYinQueries)

        self.queriesWithVALUES = {ref: self.QueryGenerator.generate_target_query(
                                        "template_VALUES",
                                        [c for c in self.constraints if c.path == self.referencedShapes[ref]],
                                        self.targetQueryNoPref,
                                        self.includePrefixes,
                                        self.ORDERBYinQueries) for ref in self.referencedShapes.keys()}

        self.queriesWithFILTER_NOT_IN = {ref: self.QueryGenerator.generate_target_query(
                                        "template_FILTER_NOT_IN",
                                        [c for c in self.constraints if c.path == self.referencedShapes[ref]],
                                        self.targetQueryNoPref,
                                        self.includePrefixes,
                                        self.ORDERBYinQueries) for ref in self.referencedShapes.keys()}

    def computeConstraintQueries(self):
        min_constraints = [c for c in self.constraints if c.min != -1]
        max_constraints = [c for c in self.constraints if c.max != -1]

        subquery = self.QueryGenerator.generate_local_subquery(min_constraints)

        # Build a unique set of triples (+ filter) for all min constraints
        min_id = self.constraintsId + "_pos"
        self.minQuery = self.QueryGenerator.generate_query(
                min_id,
                [c for c in min_constraints if c.getShapeRef() is not None],
                self.useSelectiveQueries,
                self.targetQueryNoPref,
                self.includePrefixes,
                self.ORDERBYinQueries,
                subquery
        )

        # Build one set of triples (+ filter) for each max constraint (only one max constraint per query is allowed)
        max_ids = [self.constraintsId + "_max_" + str(i) for i in range(1, len(max_constraints) + 1)]
        for i, max_c in enumerate(max_constraints):
            self.maxConstrId[max_c] = self.constraintsId + "_max_" + str(i+1)

        i = itertools.count()
        self.maxQueries = [self.QueryGenerator.generate_query(
                                        max_ids[next(i)],
                                        [c],
                                        self.useSelectiveQueries,
                                        self.targetQueryNoPref,
                                        self.includePrefixes,
                                        self.ORDERBYinQueries,
                                        subquery) for c in max_constraints]

        self.predicates = self.__compute_predicate_set(min_id, max_ids)
        self.__compute_max_queries_to_skip()
        self.__remove_unevaluated_max_queries()
        self.rulePattern = self.__compute_rule_pattern()

    def __compute_rule_pattern(self):
        """ Computes shape rule pattern """
        focus_node_var = VariableGenerator.getFocusNodeVar()
        head = (self.id, focus_node_var, True)

        return RulePattern(head, self.__get_disjunct_rp_body())

    def __get_disjunct_rp_body(self):
        focus_node_var = VariableGenerator.getFocusNodeVar()
        min_query = [(self.minQuery.get_id(), focus_node_var, True)]
        max_queries = [(s, focus_node_var, False) for s in [q.get_id() for q in self.maxQueries]]
        return min_query + max_queries

    def addParentShape(self, name):
        """ Adds name of incoming neighbor shape in the schema """
        return self.parentShapes.add(name)

    def get_parent_shapes(self):
        return self.parentShapes

    def get_valid_targets(self):
        return self.targets["valid"]

    def get_invalid_targets(self):
        return self.targets["violated"]

    def __compute_max_queries_to_skip(self):
        """
        Creates a dictionary which keys are the names of out-neighbor shapes (defined in max inter-shape constraints)
        of this shape, and the dictionary values are the respective max values of each constraint.
        """
        for max_c in self.get_constraints():
            if max_c.max != -1 and max_c.shapeRef is not None:
                for min_c in self.get_constraints():
                    if min_c.min != -1 and min_c.shapeRef == max_c.shapeRef:
                        self.maxValidRefs[max_c.shapeRef] = max_c.max
                        for constrRef, query_id in self.maxConstrId.items():
                            if constrRef.shapeRef == max_c.shapeRef:
                                self.skippedQueriesIds.add(query_id)

    def __remove_unevaluated_max_queries(self):
        """ Filters max queries to be evaluated against the SPARQL endpoint by excluding needless evaluations """
        self.maxQueries = list(filter(lambda q: q.get_id() not in self.skippedQueriesIds, self.maxQueries))

    def get_max_query_valid_refs(self):
        return self.maxValidRefs

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
