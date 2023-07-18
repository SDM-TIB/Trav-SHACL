# -*- coding: utf-8 -*-
from __future__ import annotations

__author__ = 'Monica Figuera and Philipp D. Rohde'

from typing import TYPE_CHECKING

from TravSHACL.constraints.MaxOnlyConstraint import MaxOnlyConstraint

if TYPE_CHECKING:
    from TravSHACL.core.Shape import Shape

from TravSHACL.utils.VariableGenerator import VariableGenerator
from TravSHACL.constraints.Constraint import Constraint
from TravSHACL.core.RulePattern import RulePattern


def get_target_node_statement(target_query):
    """
    Given a target query, this method returns the query body, i.e., the triple patterns.

    :param target_query: complete SPARQL query
    :return: query body of the given SPARQL query
    """
    start = target_query.index('{') + len('{')
    end = target_query.rfind('}')
    return target_query[start:end]


class Query:
    """Internal representation of a SPARQL query."""

    def __init__(self, id_, rule_pattern, sparql, inter_shape_refs=None, max_zero=False):
        """
        Creates a new instance of a SPARQL query.

        :param id_: internal query id
        :param rule_pattern: query rule pattern associated with the query
        :param sparql: actual SPARQL query, i.e., a string complying with the SPARQL protocol
        :param inter_shape_refs: used to note references to other shapes
        :param max_zero: whether this is a max zero query (needs special treatment)
        """
        self.id = id_
        self.rule_pattern = rule_pattern
        self.sparql = sparql
        self.inter_shape_refs = inter_shape_refs
        self.max_zero = max_zero

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
        :param include_prefixes: indicates whether prefixes should be included in the query
        :param include_order_by: indicates whether the ORDER BY clause will be added
        :return: generated query
        """
        if target_query is None:
            return None
        if type_ == 'plain_target':
            return self._plain_target_query(target_query, include_prefixes, include_order_by)
        elif type_ == 'template_FILTER':
            return self._target_query_filter(ref_constraint, target_query, include_prefixes, include_order_by, True), \
                   self._target_query_filter(ref_constraint, target_query, include_prefixes, include_order_by, False)

    def _plain_target_query(self, target_query, include_prefixes, include_order_by):
        """
        Generates a simple target query from the parsed target query.

        :param target_query: target query string parsed from the input file
        :param include_prefixes: indicates whether prefixes should be included in the query
        :param include_order_by: indicates whether the ORDER BY clause will be added
        :return: simple target query
        """
        prefixes = self.shape.get_prefix_string() if include_prefixes else ''
        focus_var = VariableGenerator.get_focus_node_var()
        return ''.join([prefixes,
                        target_query,
                        ' ORDER BY ?' + focus_var if include_order_by else ''])

    def _target_query_filter(self, constraint, target_query, include_prefixes, include_order_by, filter_by_valid=True):
        """
        Generates a target query for filtering based on links to valid or invalid instances of the neighboring shape.

        :param constraint: constraint that refers to this target query
        :param target_query: target query string parsed from the input file
        :param include_prefixes: indicates whether prefixes should be included in the query
        :param include_order_by: indicates whether the ORDER BY clause will be added
        :param: filter_by_valid: indicates whether valid instances will be used for filtering or invalid ones
        :return: target query with VALUES clause
        """
        prefixes = self.shape.get_prefix_string() if include_prefixes else ''
        ref_path = constraint[0].path
        focus_var = VariableGenerator.get_focus_node_var()
        target_node = get_target_node_statement(target_query)
        count = '(COUNT(DISTINCT ?inst) AS ?cnt)' if filter_by_valid else '((COUNT(DISTINCT ?inst2) - COUNT(DISTINCT ?inst)) AS ?cnt)'
        additional_triple_pattern = '  OPTIONAL { ?' + focus_var + ' ' + ref_path + ' ?inst2 . }\n' if not filter_by_valid else ''
        query = ''.join([
            prefixes,
            'SELECT DISTINCT ?' + focus_var + ' ' + count + ' WHERE {\n ',
            target_node + '\n',
            additional_triple_pattern,
            '  OPTIONAL {\n', '    VALUES ?inst { $instances_to_add$ }. \n',
            '    ?' + focus_var + ' ' + ref_path + ' ?inst .\n  }\n',
            '}\nGROUP BY ?' + focus_var, '\nORDER BY ?' + focus_var if include_order_by else ''
        ])
        return Query(None, None, query)

    # CONSTRAINT QUERIES #

    def options_query(self, constraint, target_query, include_prefixes, include_order_by):
        """
        Generates a target query including a VALUES clause to filter based on valid instances.

        :param constraint: constraint that refers to this target query
        :param target_query: target query string parsed from the input file
        :param include_prefixes: indicates whether or not prefixes should be included in the query
        :param include_order_by: indicates whether or not the ORDER BY clause will be added
        :return: target query with VALUES clause
        """
        prefixes = self.shape.get_prefix_string() if include_prefixes else ''
        focus_var = VariableGenerator.get_focus_node_var()
        target_node = get_target_node_statement(target_query)
        query_top = ''.join([prefixes, " SELECT DISTINCT ?" + focus_var + " WHERE {\n"])
        query_down = " ORDER BY ?" + focus_var if include_order_by else ''
        or_union = self.get_or_query(constraint, target_node)
        return query_top + or_union + '}' + query_down

    @staticmethod
    def get_or_query(constraints_, target_node_statement):
        """
        used to generate and combine triples required for 'or' operations

        :param constraints_: constraint to be evaluated as 'or'
        :param target_node_statement: statement for the target node
        :return: a set of unions that can be used in a query for initial validation
        """
        or_constraints = [c for c in constraints_ if c.get_shape_ref() is None]  # unsure validity with 'get_shape_ref'

        builder = QueryBuilder('tmp', None, VariableGenerator.get_focus_node_var(), False)
        or_value = 1  # used for differentiating between the constraints of different options of each or_operation
        for c in or_constraints:
            if c.options:
                or_affix = 1   # not in use yet but can be used if there are more than one constraint in an or_option
                for option in c.options:
                    if isinstance(option, MaxOnlyConstraint):
                        builder.build_clause(option, or_value, or_affix, True)
                    else:
                        builder.build_clause(option, or_value, or_affix, False)
                    or_affix += 1
                or_value += 1
        return builder.build_union(target_node_statement, VariableGenerator.get_focus_node_var())

    def generate_query(self, id_, constraints, is_selective, target_query,
                       include_prefixes, include_order_by, subquery=None):
        """
        Generates a constraint query.

        :param id_: internal query/constraint name
        :param constraints: a list of constraints that refer to this constraint query
        :param is_selective: indicates whether selective queries are used
        :param target_query: target query of the shape associated with the constraint
        :param include_prefixes: indicates whether prefixes should be included in the query
        :param include_order_by: indicates whether the ORDER BY clause will be added
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

        builder = QueryBuilder('tmp', None, VariableGenerator.get_focus_node_var(), False)

        for c in local_pos_constraints:
            builder.build_clause(c)
        return builder.get_sparql(False, True)


class QueryBuilder:
    """This class is responsible for actually building SPARQL queries for constraints."""

    def __init__(self, id_, subquery, projected_variables, is_selective, target_query=None,
                 constraints=None, include_order_by: bool = False, prefix_string: str = ''):
        """
        Creates a new instance of QueryBuilder.

        :param id_: internal query name
        :param subquery: sub-query to be included, might be None
        :param projected_variables: list of variables to be projected
        :param is_selective: indicates whether selective queries are used
        :param target_query: target query of the shape associated with the constraint
        :param constraints: a list of constraints that refer to the constraint query
        :param include_order_by: indicates whether the ORDER BY clause will be added
        :param prefix_string: prefix string for the queries being built
        """
        self.id = id_
        self.subquery = subquery
        self.projected_variables = projected_variables
        self.filters = []
        self.triples = []
        self.union_triples = []
        self.max_dict = {}

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
        self.triples.append('?' + VariableGenerator.get_focus_node_var() + ' ' + path + ' ' + obj + '.')

    def add_union_triples(self, path, obj, val_1, val_2, maxonly: bool = False, card: int = -1):
        """
        Adds a triple pattern to the constraint query.
        No subject is needed as in a constraint query all triple patterns share the same subject.

        :param path: predicate of the triple pattern
        :param obj: object of the triple pattern
        :param val_1: for union grouping(general)
        :param val_2: for local union grouping
        :param maxonly: tells if the constraint is maxonly
        :param card: cardinality restriction of the constraint to be added
        """
        if maxonly:
            self.union_triples.append(str(val_1) + '#' + str(val_2) + '#max#' + str(card) + '#?' +
                                      VariableGenerator.get_focus_node_var() + ' ' + path + ' ' + obj + '.')
        else:
            self.union_triples.append(str(val_1) + '#' + str(val_2) + '#min#' + str(card) + '#?' +
                                      VariableGenerator.get_focus_node_var() + ' ' + path + ' ' + obj + '.')

    def union_with_filters(self, union_list):
        union_list_to_keep = []
        for filter_ in self.filters:
            filter_union = []
            for entry in union_list:
                if entry.rsplit(' ', 1)[1].split('.')[0] in filter_:
                    filter_union.append(entry)
                else:
                    union_list_to_keep.append(entry)
            if filter_union:
                union_list_to_keep.append('{' + self.__get_projection_string() + ' WHERE {\n' + '\n'.join(filter_union)
                                          + '\nFILTER( \n' + filter_ + ') \n }}')
        return union_list_to_keep

    def build_union(self, target_node_statement: str, focus_node_var: str):
        """
        Builds a union pattern
        No subject is needed as in a constraint query all triple patterns share the same subject.

        """
        if self.union_triples is []:
            return
        else:
            grouping = []
            for entry in self.union_triples:
                group_number = entry.split('#', 3)[0]
                if group_number not in grouping:
                    grouping.append(group_number)

            for group in grouping:
                current_group = []
                for entry in self.union_triples:
                    if entry.split('#', 3)[0] == group:
                        if entry.split('#', 3)[2] == 'min':
                            current_group.append(self.cardinality_graph_pattern(target_node_statement, focus_node_var,
                                                           entry.split('#', 4)[4], False, entry.split('#', 4)[3]))
                        if entry.split('#', 3)[2] == 'max':
                            current_group.append(self.cardinality_graph_pattern(target_node_statement, focus_node_var,
                                                           entry.split('#', 4)[4], True, entry.split('#', 4)[3]))
                        # self.triples.remove(entry.split('#', 2)[2])
                    # entry.split('#', 2)[1] can be used for grouping if there are more than just the path constraint
                # print(current_group)
                if len(self.filters) > 0:
                    current_group = self.union_with_filters(current_group)

                self.triples.append(self.union_group(current_group))
        return '\n'.join(self.triples)

    @staticmethod
    def cardinality_graph_pattern(target_node_statement: str, focus_node_var: str,
                                  triple_pattern: str, max_: bool, card: int):
        """
        Creates a subquery for cardinality constraints to be used in OR constraints.

        :param target_node_statement: The statement for the target node of the constraint
        :param focus_node_var: The variable for the focus node (usually x)
        :param triple_pattern: The triple pattern of the cardinality constraint
        :param max_: Indicates whether the constraint is a max cardinality constraint
        :param card: The cardinality restriction of the constraint
        """
        cgp = '{ SELECT DISTINCT ?' + focus_node_var + ' WHERE {\n' + target_node_statement + ' .\n'
        if max_:
            cgp += 'OPTIONAL { ' + triple_pattern + '}'
        else:
            cgp += triple_pattern
        cgp += '\n}\nGROUP BY ?' + focus_node_var + '\nHAVING (COUNT(DISTINCT ?' + triple_pattern.split('?', 2)[2][:-1] + ') '
        if max_:
            cgp += '<= '
        else:
            cgp += '>= '
        cgp += str(card) + ') }'
        return cgp

    @staticmethod
    def union_group(triples_to_join):
        """
        Add a filter based on a datatype.

        :param triples_to_join: list containing triples that should observe unions
        """
        return '\n UNION \n'.join(triples_to_join)

    def add_datatype_filter(self, variable, datatype, is_pos):
        """
        Add a filter based on a datatype.

        :param variable: the variable the filter should be added for
        :param datatype: the expected datatype
        :param is_pos: indicated whether this is a positive constraint
        """
        s = 'datatype(?' + variable + ') = ' + datatype
        self.filters.append(s if is_pos else '!(' + s + ')')

    def add_constant_filter(self, variable, constant, is_pos):
        """
        Add a filter for a constant.

        :param variable: the variable the filter should be added for
        :param constant: the constant value the variable should be assigned
        :param is_pos: indicated whether this is a positive constraint
        """
        s = variable + ' = ' + constant
        self.filters.append(s if is_pos else '!(' + s + ')')

    def get_sparql(self, include_prefixes, is_subquery):
        """
        Get the SPARQL query corresponding to the current state of the QueryBuilder.

        :param include_prefixes: indicates whether prefixes should be included in the query
        :param is_subquery: indicates whether the query is considered to be a sub-query
        :return: the SPARQL query as a string
        """
        if is_subquery:
            return self.__get_query(False)  # create subquery

        prefixes = self.prefix_string if include_prefixes else ''
        if isinstance(self.subquery, str):
            if self.subquery == '':
                self.subquery = None
        outer_query_closing_braces = ''.join(['}\n' if self.subquery is not None else '',
                                              '}' if self.get_triple_patterns() != '' and self.subquery is not None else '',
                                              '}' if self.get_triple_patterns() != '' else ''])

        selective_closing_braces = '}}' if self.include_selectivity and self.target_query is not None else ''

        if len(self.constraints) == 1 and isinstance(self.constraints[0], MaxOnlyConstraint) and self.constraints[
            0].get_shape_ref() is None:
            target_node = ''
            if self.include_selectivity and self.target_query is not None:
                target_node = get_target_node_statement(self.target_query) + '.\n'

            if self.constraints[0].get_value() is not None:
                pred = self.constraints[0].path
                obj = self.constraints[0].get_value()
                return ''.join([prefixes,
                                self.__get_projection_string(),
                                ' WHERE {\n', target_node,
                                '?', VariableGenerator.get_focus_node_var(), ' ', pred, ' ', obj, '.\n}',
                                ' ORDER BY ?' + VariableGenerator.get_focus_node_var() if self.include_ORDERBY else ''])
            else:
                if self.triples:
                    return ''.join([prefixes,
                                    self.__get_projection_string(),
                                    ' WHERE {\n', target_node,
                                    self.triples[0], '\n} GROUP BY ?',
                                    VariableGenerator.get_focus_node_var(),
                                    ' HAVING (COUNT(DISTINCT ?', self.triples[0].rsplit('?', 1)[1][:-1], ') >= ',
                                    str(self.constraints[0].max + 1), ')',
                                    ' ORDER BY ?' + VariableGenerator.get_focus_node_var() if self.include_ORDERBY else ''])
        query = ''.join([prefixes,
                         self.__get_selective(),
                         self.__get_query(include_prefixes),
                         self.subquery if self.subquery is not None else '',
                         outer_query_closing_braces,
                         selective_closing_braces,
                         ' ORDER BY ?' + VariableGenerator.get_focus_node_var() if self.include_ORDERBY else ''])
        return query

    def __get_query(self, include_prefixes):
        """
        Internal method of the QueryBuilder to generate the SPARQL query string.

        :param include_prefixes: indicates whether prefixes should be included in the query
        :return: the SPARQL query as a string
        """
        temp_string = ''
        if include_prefixes:
            if '_pos' in self.id or '_max_' in self.id:
                # add VALUES clause to external query
                temp_string = '$filter_clause_to_add$'

        triple_patterns = self.get_triple_patterns()
        if isinstance(self.subquery, str):
            if self.subquery == '':
                self.subquery = None
        if triple_patterns != '':
            return ''.join([self.__get_projection_string(),
                            ' WHERE {\n',
                            temp_string,
                            triple_patterns,
                            '\n', '{\n' if self.subquery is not None else ''])
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
                            ' WHERE {\n',
                            target_node + '. {\n'])
        return ''

    def __get_projection_string(self):
        """
        Internal method of the QueryBuilder for generating the SELECT clause.

        :return: the SELECT clause of the query to be built
        """
        return 'SELECT DISTINCT ' + ' '.join(['?' + v for v in self.projected_variables])

    def get_triple_patterns(self):
        """
        Gets all triple patterns belonging to the query that is currently being built.

        :return: all triple patterns of the query
        """
        triple_string = '\n'.join(self.triples)

        if len(self.filters) == 0:
            return triple_string

        return triple_string + self.generate_filter_string()

    def generate_filter_string(self):
        """
        Generates the filter string for the filters to be applied to the query.

        :return: a string for the filters to be applied
        """
        if len(self.filters) == 0:
            return ''

        return '\nFILTER(\n' + (self.filters[0] if len(self.filters) == 1 else ' &&\n'.join(self.filters)) + ')'

    def add_cardinality_filter(self, variables):
        """
        Adds a filter on the cardinality of a variable.

        :param variables: list of variables to add cardinality filters for
        """
        for i in range(0, len(variables)):
            for j in range(i + 1, len(variables)):
                self.filters.append('?' + variables[i] + ' != ?' + variables[j])

    def build_clause(self, c, or_value: int = 0, or_affix: int = 0, maxonly: bool = False):
        """
        Adds the necessary information to the QueryBuilder for a given constraint.

        :param c: the constraint to be included in the query
        :param or_value: used in the case of multiple 'or' for triple grouping
        :param or_affix: used in the case of more than one or triple within an option in an 'or' operation
        :param maxonly: tells if the constraint is maxonly
        """
        variables = c.get_variables()
        if not maxonly:
            if isinstance(c, Constraint):
                path = c.path
                if c.get_value() is not None:  # if there is fixed value for the object
                    if or_value > 0:
                        self.add_union_triples(path, c.get_value(), or_value, or_affix)
                    else:
                        self.add_triple(path, c.get_value())
                    return

                if or_value > 0:
                    v = variables[0]
                    self.add_union_triples(path, '?' + v, or_value, or_affix, card=c.min)
                else:
                    for v in variables:
                        if c.get_shape_ref() is not None:  # if there is an existing reference to another shape
                            self.inter_shape_refs[v] = c.get_shape_ref()
                            self.triples.append('\n$inter_shape_type_to_add$')
                        self.add_triple(path, '?' + v)

            if c.get_value() is not None:
                self.add_constant_filter(
                    variables.iterator().next(),
                    c.get_value().get(),
                    c.get_is_pos()
                )

            if c.get_datatype() is not None:
                for v in variables:
                    self.add_datatype_filter(v, c.get_datatype(), c.get_is_pos())

            if len(variables) > 1 and or_value == 0:
                self.add_cardinality_filter(variables)

        else:
            if isinstance(c, Constraint):
                path = c.path
                v = variables[0]        # this limits the use of max_constraints
                self.add_union_triples(path, '?' + v, or_value, or_affix, True, card=c.max)

    def build_query(self, rule_pattern, include_prefixes):
        """
        Generate a Query object based on the current state of the QueryBuilder.

        :param rule_pattern: the query rule pattern associated with the query
        :param include_prefixes: indicates whether prefixes should be included in the query
        """
        max_zero_query = False
        for c in self.constraints:
            if c.max == 0:
                max_zero_query = True

        return Query(
            self.id,
            rule_pattern,
            self.get_sparql(include_prefixes, False),
            self.inter_shape_refs,
            max_zero_query
        )
