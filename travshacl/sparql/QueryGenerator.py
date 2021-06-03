# -*- coding: utf-8 -*-
from __future__ import annotations

__author__ = "Monica Figuera"

from typing import TYPE_CHECKING

from travshacl.constraints.MaxOnlyConstraint import MaxOnlyConstraint
from travshacl.constraints.MinOnlyConstraint import MinOnlyConstraint

if TYPE_CHECKING:
    from travshacl.core.Shape import Shape

from travshacl.utils.VariableGenerator import VariableGenerator
from travshacl.constraints.Constraint import Constraint
from travshacl.core.RulePattern import RulePattern


def get_target_node_statement(target_query):
    """
    Given a target query, this method returns the query body, i.e., the triple patterns.

    :param target_query: complete SPARQL query
    :return: query body of the given SPARQL query
    """
    start = target_query.index("{") + len("{")
    end = target_query.rfind("}")
    return target_query[start:end]


class Query:
    """Internal representation of a SPARQL query."""

    def __init__(self, id_, rule_pattern, sparql, inter_shape_refs=None):
        """
        Creates a new instance of a SPARQL query.

        :param id_: internal query id
        :param rule_pattern: query rule pattern associated with the query
        :param sparql: actual SPARQL query, i.e., a string complying with the SPARQL protocol
        :param inter_shape_refs: used to note references to other shapes
        """
        self.id = id_
        self.rule_pattern = rule_pattern
        self.sparql = sparql
        self.inter_shape_refs = inter_shape_refs

    def get_id(self):
        return self.id

    def get_rule_pattern(self):
        return self.rule_pattern

    def get_sparql(self):
        return self.sparql

    def get_inter_shape_refs_names(self):
        return self.inter_shape_refs


class QueryGenerator:
    """This class is responsible for generating target and constraint queries."""

    def __init__(self, shape: Shape):
        self.shape = shape

    # TARGET QUERIES #

    def generate_target_query(self, type_, ref_constraint, target_query, include_prefixes, include_order_by):
        """
        Generates a SPARQL target query. It can be a simple query with only one triple pattern or contain
        a VALUES or FILTER NOT IN clause to filter valid or invalid instances directly during the target extraction.

        :param type_: indicates the type of target query to generate
        :param ref_constraint: might hold a list of constraints that refer to this target query
        :param target_query: target query string parsed from the input file
        :param include_prefixes: indicates whether or not prefixes should be included in the query
        :param include_order_by: indicates whether or not the ORDER BY clause will be added
        :return: generated query
        """
        if target_query is None:
            return None
        if type_ == "plain_target":
            return self._plain_target_query(target_query, include_prefixes, include_order_by)
        elif type_ == "template_VALUES":
            return self._values_target_query(ref_constraint, target_query, include_prefixes, include_order_by)
        elif type_ == "template_FILTER_NOT_IN":
            return self._filter_not_in_target_query(ref_constraint, target_query, include_prefixes, include_order_by)

    def _plain_target_query(self, target_query, include_prefixes, include_order_by):
        """
        Generates a simple target query from the parsed target query.

        :param target_query: target query string parsed from the input file
        :param include_prefixes: indicates whether or not prefixes should be included in the query
        :param include_order_by: indicates whether or not the ORDER BY clause will be added
        :return: simple target query
        """
        prefixes = self.shape.get_prefix_string() if include_prefixes else ''
        focus_var = VariableGenerator.get_focus_node_var()
        return ''.join([prefixes,
                        target_query,
                        " ORDER BY ?" + focus_var if include_order_by else ''])

    def _values_target_query(self, constraint, target_query, include_prefixes, include_order_by):
        """
        Generates a target query including a VALUES clause to filter based on valid instances.

        :param constraint: constraint that refers to this target query
        :param target_query: target query string parsed from the input file
        :param include_prefixes: indicates whether or not prefixes should be included in the query
        :param include_order_by: indicates whether or not the ORDER BY clause will be added
        :return: target query with VALUES clause
        """
        prefixes = self.shape.get_prefix_string() if include_prefixes else ''
        ref_path = constraint[0].path
        focus_var = VariableGenerator.get_focus_node_var()
        target_node = get_target_node_statement(target_query)
        query = ''.join([prefixes,
                         "SELECT DISTINCT ?" + focus_var + " WHERE {\n",
                         "VALUES ?inst { $instances_to_add$ }. \n",
                         "?" + focus_var + " " + ref_path + " ?inst.\n",
                         target_node + "\n}\n",
                         " ORDER BY ?" + focus_var if include_order_by else ''])
        return Query(None, None, query)

    def _filter_not_in_target_query(self, constraint, target_query, include_prefixes, include_order_by):
        """
        Generates a target query including a FILTER NOT IN clause to filter based on invalid instances.

        :param constraint: constraint that refers to this target query
        :param target_query: target query string parsed from the input file
        :param include_prefixes: indicates whether or not prefixes should be included in the query
        :param include_order_by: indicates whether or not the ORDER BY clause will be added
        :return: target query with FILTER NOT IN clause
        """
        prefixes = self.shape.get_prefix_string() if include_prefixes else ''
        ref_path = constraint[0].path
        focus_var = VariableGenerator.get_focus_node_var()
        target_node = get_target_node_statement(target_query)
        query = ''.join([prefixes,
                         "SELECT DISTINCT ?" + focus_var + " WHERE {\n",
                         "?" + focus_var + " " + ref_path + " ?inst.\n",
                         target_node + "\n",
                         "FILTER (?inst NOT IN ( $instances_to_add$ )). }\n",
                         " ORDER BY ?" + focus_var if include_order_by else ''])
        return Query(None, None, query)

    # CONSTRAINT QUERIES #

    def generate_query(self, id_, constraints, is_selective, target_query,
                       include_prefixes, include_order_by, subquery=None):
        """
        Generates a constraint query.

        :param id_: internal query/constraint name
        :param constraints: a list of constraints that refer to this constraint query
        :param is_selective: indicates whether or not selective queries are used
        :param target_query: target query of the shape associated with the constraint
        :param include_prefixes: indicates whether or not prefixes should be included in the query
        :param include_order_by: indicates whether or not the ORDER BY clause will be added
        :param subquery: might hold a sub-query to be used in the constraint query
        :return: the generated constraint query
        """
        rp = self.compute_rule_pattern(constraints, id_)
        builder = QueryBuilder(id_, subquery, rp.variables, is_selective, target_query,
                               constraints, include_order_by, self.shape.get_prefix_string())
        for c in constraints:
            builder.build_clause(c)
        return builder.build_query(rp, include_prefixes)

    @staticmethod
    def compute_rule_pattern(constraints, id_):
        """
        Computes the query rule patterns for the given constraints.

        :param constraints: a list of constraints to compute the rule patterns for
        :param id_: the internal constraint query name associated with the constraints
        :return: query rule pattern for the constraints
        """
        body = []
        for c in constraints:
            body = body + c.compute_rule_pattern_body()

        return RulePattern(
            head=(id_, VariableGenerator.get_focus_node_var(), True),
            body=body
        )

    @staticmethod
    def generate_local_subquery(positive_constraints):
        """
        Generates a local sub-query.

        :param positive_constraints: positive constraints
        :return: sub-query including the constraints
        """
        local_pos_constraints = [c for c in positive_constraints if c.get_shape_ref() is None]

        if len(local_pos_constraints) == 0:
            return None  # optional empty

        builder = QueryBuilder("tmp", None, VariableGenerator.get_focus_node_var(), False)

        for c in local_pos_constraints:
            builder.build_clause(c)

        return builder.get_sparql(False, True)


class QueryBuilder:
    """This class is responsible of actually building SPARQL queries for constraints."""

    def __init__(self, id_, subquery, projected_variables, is_selective, target_query=None,
                 constraints=None, include_order_by: bool = False, prefix_string: str = ''):
        """
        Creates a new instance of QueryBuilder.

        :param id_: internal query name
        :param subquery: sub-query to be included, might be None
        :param projected_variables: list of variables to be projected
        :param is_selective: indicates whether or not selective queries are used
        :param target_query: target query of the shape associated with the constraint
        :param constraints: a list of constraints that refer to the constraint query
        :param include_order_by: indicates whether or not the ORDER BY clause will be added
        :param prefix_string: prefix string for the queries being built
        """
        self.id = id_
        self.subquery = subquery
        self.projected_variables = projected_variables
        self.filters = []
        self.triples = []

        self.include_selectivity = is_selective
        self.target_query = target_query
        self.constraints = constraints
        self.include_ORDERBY = include_order_by
        self.inter_shape_refs = {}
        self.prefix_string = prefix_string

    def add_triple(self, path, obj):
        """
        Adds a triple pattern to the constraint query.
        No subject is needed as in a constraint query all triple patterns share the same subject.

        :param path: predicate of the triple pattern
        :param obj: object of the triple pattern
        """
        self.triples.append("?" + VariableGenerator.get_focus_node_var() + " " + path + " " + obj + ".")

    def add_datatype_filter(self, variable, datatype, is_pos):
        """
        Add a filter based on a datatype.

        :param variable: the variable the filter should be added for
        :param datatype: the expected datatype
        :param is_pos: indicated whether or not this is a positive constraint
        """
        s = "datatype(?" + variable + ") = " + datatype
        self.filters.append(s if is_pos else "!(" + s + ")")

    def add_constant_filter(self, variable, constant, is_pos):
        """
        Add a filter for a constant.

        :param variable: the variable the filter should be added for
        :param constant: the constant value the variable should be assigned
        :param is_pos: indicated whether or not this is a positive constraint
        """
        s = variable + " = " + constant
        self.filters.append(s if is_pos else "!(" + s + ")")

    def get_sparql(self, include_prefixes, is_subquery):
        """
        Get the SPARQL query corresponding to the current state of the QueryBuilder.

        :param include_prefixes: indicates whether or not prefixes should be included in the query
        :param is_subquery: indicates whether or not the query is considered to be a sub-query
        :return: the SPARQL query as a string
        """
        if is_subquery:
            return self.__get_query(False)  # create subquery

        prefixes = self.prefix_string if include_prefixes else ''
        outer_query_closing_braces = ''.join(["}\n" if self.subquery is not None else '',
                                              "}" if self.get_triple_patterns() != '' and self.subquery is not None else '',
                                              "}" if self.get_triple_patterns() != '' else ''])
        selective_closing_braces = "}}" if self.include_selectivity and self.target_query is not None else ''

        query = ''.join([prefixes,
                        self.__get_selective(),
                        self.__get_query(include_prefixes),
                        self.subquery if self.subquery is not None else '',
                        outer_query_closing_braces,
                        selective_closing_braces,
                        " ORDER BY ?" + VariableGenerator.get_focus_node_var() if self.include_ORDERBY else ''])
        return query

    def __get_query(self, include_prefixes):
        """
        Internal method of the QueryBuilder to generated the SPARQL query string.

        :param include_prefixes: indicates whether or not prefixes should be included in the query
        :return: the SPARQL query as a string
        """
        temp_string = ''
        if include_prefixes:
            if "_pos" in self.id or "_max_" in self.id:
                # add VALUES clause to external query
                temp_string = "$filter_clause_to_add$"

        triple_patterns = self.get_triple_patterns()
        if triple_patterns != '':
            return ''.join([self.__get_projection_string(),
                            " WHERE {\n",
                            temp_string,
                            triple_patterns,
                            "\n", "{\n" if self.subquery is not None else ''])
        else:
            return ''

    def __get_selective(self):
        """
        Internal method of the QueryBuilder to generate selective constraint queries.

        :return: a SPARQL query including the target definition of the shape associated to the constraint query
        """
        if self.include_selectivity and self.target_query is not None:
            target_node = get_target_node_statement(self.target_query)
            return ''.join([self.__get_projection_string(),
                            " WHERE {\n",
                            target_node + ". {\n"])
        return ''

    def __get_projection_string(self):
        """
        Internal method of the QueryBuilder for generating the SELECT clause.

        :return: the SELECT clause of the query to be built
        """
        return "SELECT DISTINCT " + " ".join(["?" + v for v in self.projected_variables])

    def get_triple_patterns(self):
        """
        Gets all triple patterns belonging to the query that is currently being built.

        :return: all triple patterns of the query
        """
        if self.constraints is not None and len(self.constraints) > 1 and isinstance(self.constraints[0], MaxOnlyConstraint):
            triple_string = "\nUNION\n".join(self.triples)
            print("triple string:\n" + triple_string + "\n*********")
        else:
            triple_string = "\n".join(self.triples)

        if len(self.filters) == 0:
            return triple_string

        return triple_string + self.generate_filter_string()

    def generate_filter_string(self):
        """
        Generates the filter string for the filters to be applied to the query.

        :return: a string for the filters to be applied
        """
        if len(self.filters) == 0:
            return ""

        return "\nFILTER(\n" + (self.filters[0] if len(self.filters) == 1 else " &&\n".join(self.filters)) + ")"

    def add_cardinality_filter(self, variables):
        """
        Adds a filter on the cardinality of a variable.

        :param variables: list of variables to add cardinality filters for
        """
        for i in range(0, len(variables)):
            for j in range(i + 1, len(variables)):
                self.filters.append("?" + variables[i] + " != ?" + variables[j])

    def build_clause(self, c):
        """
        Adds the necessary information to the QueryBuilder for a given constraint.

        :param c: the constraint to be included in the query
        """
        variables = c.get_variables()

        if isinstance(c, Constraint):
            path = c.path

            if c.get_value() is not None:  # if there is an existing reference to another shape
                self.add_triple(path, c.get_value())
                return

            for v in variables:
                if c.get_shape_ref() is not None and c.max == 0:
                    self.inter_shape_refs[v] = c.get_shape_ref()
                    self.triples.append("\n$inter_shape_type_to_add$")

                if c.get_shape_ref() is not None or len(variables) == 1:
                    self.add_triple(path, "?" + v)

        if c.get_value() is not None:
            self.add_constant_filter(
                variables.iterator().next(),
                c.get_value().get(),
                c.get_is_pos()
            )

        if c.get_datatype() is not None:
            for v in variables:
                self.add_datatype_filter(v, c.get_datatype(), c.get_is_pos())

        if len(variables) > 1:
            if c.get_shape_ref() is not None:
                self.add_cardinality_filter(variables)
            else:
                focus_var = VariableGenerator.get_focus_node_var()
                var = variables[0]
                triple = "{ SELECT ?" + focus_var + " COUNT(?" + var + " AS ?cnt) WHERE { ?" + \
                         focus_var + " " + c.path + " ?" + var + " . } GROUP BY ?" + focus_var + \
                         " HAVING (COUNT(?" + var + ") > " + str(len(variables) - 1) + ") }"
                self.triples.append(triple)

    def build_query(self, rule_pattern, include_prefixes):
        """
        Generate a Query object based on the current state of the QueryBuilder.

        :param rule_pattern: the query rule pattern associated with the query
        :param include_prefixes: indicates whether or not prefixes should be included in the query
        """
        return Query(
            self.id,
            rule_pattern,
            self.get_sparql(include_prefixes, False),
            self.inter_shape_refs
        )
