# -*- coding: utf-8 -*-
__author__ = "Monica Figuera and Philipp D. Rohde"

import itertools

from travshacl.utils.VariableGenerator import VariableGenerator
from travshacl.core.RulePattern import RulePattern
from travshacl.sparql.QueryGenerator import QueryGenerator


class Shape:
    """This class represents a SHACL shape."""

    def __init__(self, id_, target_def, target_type, target_query, constraints, constraints_id, referenced_shapes,
                 use_selective_queries, max_split_size, order_by_in_queries, include_sparql_prefixes):
        """
        Creates a new Shape instance representing a SHACL shape that needs to be evaluated.

        :param id_: the name of the shape
        :param target_def: target definition of the shape
        :param target_type: indicates the target type of the shape, e.g., class or node
        :param target_query: target query of the shape
        :param constraints: the constraints belonging to the shape
        :param constraints_id: the constraint ids
        :param referenced_shapes: a list of shapes that is referenced from this shape
        :param use_selective_queries: indicates whether or not selective queries are used
        :param max_split_size: maximum number of instances per query
        :param order_by_in_queries: indicates whether or not to use the ORDER BY clause
        :param include_sparql_prefixes: indicates whether or not to include SPARQL prefixes in queries for the shape
        """
        self.id = id_
        self.constraints = constraints
        self.constraintsId = constraints_id
        self.predicates = []
        self.targetDef = target_def
        self.targetType = target_type          # Might be None
        self.targetQuery = target_query        # Might be None
        self.targetQueryNoPref = target_query  # Might be None
        self.rulePattern = ()
        self.satisfied = None
        self.inDegree = None
        self.outDegree = None

        self.minQuery = None
        self.maxQueries = None
        self.predicates = []
        self.maxValidRefs = {}
        self.skippedQueriesIds = set()

        self.referencedShapes = referenced_shapes
        self.parentShapes = set()
        self.queriesWithVALUES = {}
        self.queriesWithFILTER_NOT_IN = {}  # complement of VALUES
        self.targets = {"valid": set(), "violated": set()}

        self.useSelectiveQueries = use_selective_queries
        self.querySplitThreshold = max_split_size
        self.ORDERBYinQueries = order_by_in_queries
        self.includePrefixes = include_sparql_prefixes
        self.maxConstrId = {}

        self.QueryGenerator = QueryGenerator()
        self.__compute_target_queries()

    def get_id(self):
        return self.id

    def set_degree(self, in_, out_):
        self.inDegree = in_
        self.outDegree = out_

    def __compute_predicate_set(self, min_query_id, max_queries_ids):
        """ Returns the ids of the queries for this shape """
        return [self.id] + [self.id + "_d1"] + [min_query_id] + [q for q in max_queries_ids]

    def get_target_query(self):
        return self.targetQuery

    def get_constraints(self):
        return self.constraints

    def get_number_constraints(self):
        """ Gets the number of constraints belonging to this shape """
        return len(self.constraints)

    def get_shape_refs(self):
        return [c.get_shape_ref() for c in self.constraints if c.get_shape_ref() is not None]

    def get_rule_pattern(self):
        return self.rulePattern

    def get_query_split_threshold(self):
        return self.querySplitThreshold

    def __compute_target_queries(self):
        """Internal method to compute the target query of the shape."""
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

    def compute_constraint_queries(self):
        """Computes all constraint queries for the shape."""
        min_constraints = [c for c in self.constraints if c.min != -1]
        max_constraints = [c for c in self.constraints if c.max != -1]

        subquery = self.QueryGenerator.generate_local_subquery(min_constraints)

        # Build a unique set of triples (+ filter) for all min constraints
        min_id = self.constraintsId + "_pos"
        self.minQuery = self.QueryGenerator.generate_query(
                min_id,
                [c for c in min_constraints if c.get_shape_ref() is not None],
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
        focus_node_var = VariableGenerator.get_focus_node_var()
        head = (self.id, focus_node_var, True)

        return RulePattern(head, self.__get_disjunct_rp_body())

    def __get_disjunct_rp_body(self):
        focus_node_var = VariableGenerator.get_focus_node_var()
        min_query = [(self.minQuery.get_id(), focus_node_var, True)]
        max_queries = [(s, focus_node_var, False) for s in [q.get_id() for q in self.maxQueries]]
        return min_query + max_queries

    def add_parent_shape(self, name):
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
