# -*- coding: utf-8 -*-
__author__ = "Monica Figuera"

from validation.core.RulePattern import RulePattern
from validation.core.Query import Query
from validation.VariableGenerator import VariableGenerator
from validation.sparql.SPARQLPrefixHandler import getPrefixString
from validation.constraints.Constraint import Constraint


def get_target_node_statement(target_query):
    start = target_query.index("{") + len("{")
    end = target_query.index("}", start)
    return target_query[start:end]


class QueryGenerator:
    def __init__(self):
        pass

    # TARGET QUERIES #

    def generate_target_query(self, id, ref_constraint, target_query, include_prefixes, include_ORDERBY):
        if target_query is None:
            return None
        if id == "plain_target":
            return self.plain_target_query(target_query, include_prefixes, include_ORDERBY)
        elif id == "template_VALUES":
            return self.VALUES_target_query(ref_constraint, target_query, include_prefixes, include_ORDERBY)
        elif id == "template_FILTER_NOT_IN":
            return self.FILTER_NOT_IN_target_query(ref_constraint, target_query, include_prefixes, include_ORDERBY)

    @staticmethod
    def plain_target_query(target_query, include_prefixes, include_ORDERBY):
        prefixes = getPrefixString() if include_prefixes else ''
        focus_var = VariableGenerator.getFocusNodeVar()
        return ''.join([prefixes,
                        target_query,
                        " ORDER BY ?" + focus_var if include_ORDERBY else ''])

    @staticmethod
    def VALUES_target_query(constraint, target_query, include_prefixes, include_ORDERBY):
        prefixes = getPrefixString() if include_prefixes else ''
        ref_path = constraint[0].path
        focus_var = VariableGenerator.getFocusNodeVar()
        target_node = get_target_node_statement(target_query)
        query = ''.join([prefixes,
                         "SELECT DISTINCT ?" + focus_var + " WHERE {\n",
                         "VALUES ?inst { $to_be_replaced$ }. \n",
                         "?" + focus_var + " " + ref_path + " ?inst.\n",
                         target_node + "\n}\n",
                         " ORDER BY ?" + focus_var if include_ORDERBY else ''])
        return Query(None, None, query)

    @staticmethod
    def FILTER_NOT_IN_target_query(constraint, target_query, include_prefixes, include_ORDERBY):
        prefixes = getPrefixString() if include_prefixes else ''
        ref_path = constraint[0].path
        focus_var = VariableGenerator.getFocusNodeVar()
        target_node = get_target_node_statement(target_query)
        query = ''.join([prefixes,
                         "SELECT DISTINCT ?" + focus_var + " WHERE {\n",
                         "?" + focus_var + " " + ref_path + " ?inst.\n",
                         target_node + "\n",
                         "FILTER (?inst NOT IN ( $to_be_replaced$ )). }\n",
                         " ORDER BY ?" + focus_var if include_ORDERBY else ''])
        return Query(None, None, query)

    # CONSTRAINT QUERIES #

    def generate_query(self, id, constraints, is_selective, target_query, include_prefixes, include_ORDERBY, subquery=None):
        rp = self.compute_rule_pattern(constraints, id)
        builder = QueryBuilder(id, subquery, rp.getVariables(), is_selective, target_query, constraints, include_ORDERBY)
        for c in constraints:
            builder.build_clause(c)
        return builder.build_query(rp, include_prefixes)

    @staticmethod
    def compute_rule_pattern(constraints, id):
        body = []
        for c in constraints:
            body = body + c.computeRulePatternBody()

        return RulePattern(
                (
                    id,
                    VariableGenerator.getFocusNodeVar(),
                    True
                ),
                body
        )

    @staticmethod
    def generate_local_subquery(positive_constraints):
        local_pos_constraints = [c for c in positive_constraints if c.getShapeRef() is None]

        if len(local_pos_constraints) == 0:
            return None  # optional empty

        builder = QueryBuilder(
                "tmp",
                None,
                VariableGenerator.getFocusNodeVar(),
                False
        )

        for c in local_pos_constraints:
            builder.build_clause(c)

        return builder.get_SPARQL(False, True)


class QueryBuilder:
    def __init__(self, id, subquery, projected_variables, is_selective, target_query=None, constraints=None,
                 include_ORDERBY=None):
        self.id = id
        self.subquery = subquery
        self.projected_variables = projected_variables
        self.filters = []
        self.triples = []

        self.include_selectivity = is_selective
        self.target_query = target_query
        self.constraints = constraints
        self.include_ORDERBY = include_ORDERBY if include_ORDERBY is not None else False

    def add_triple(self, path, object):
        self.triples.append(
                "?" + VariableGenerator.getFocusNodeVar() + " " +
                path + " " +
                object + "."
        )

    def add_datatype_filter(self, variable, datatype, is_pos):
        s = self.__get_datatype_filter(variable, datatype)
        self.filters.append(s if is_pos else "!(" + s + ")")

    @staticmethod
    def __get_datatype_filter(variable, datatype):
        return "datatype(?" + variable + ") = " + datatype

    def add_constant_filter(self, variable, constant, is_pos):
        s = variable + " = " + constant
        self.filters.append(s if is_pos else "!(" + s + ")")

    def get_SPARQL(self, include_prefixes, is_subquery):
        if is_subquery:
            return self.get_query(False)  # create subquery

        prefixes = getPrefixString() if include_prefixes else ''
        outer_query_closing_braces = ''.join(["}\n" if self.subquery is not None else '',
                                              "}" if self.get_triple_patterns() != '' and self.subquery is not None else '',
                                              "}" if self.get_triple_patterns() != '' else ''])
        selective_closing_braces = "}}" if self.include_selectivity else ''

        return ''.join([prefixes,
                        self.get_selective(),
                        self.get_query(include_prefixes),
                        self.subquery if self.subquery is not None else '',
                        outer_query_closing_braces,
                        selective_closing_braces,
                        " ORDER BY ?" + VariableGenerator.getFocusNodeVar() if self.include_ORDERBY else ''])

    def get_query(self, include_prefixes):
        temp_string = ''
        if include_prefixes:
            if "_pos" in self.id or "_max_" in self.id:
                # add VALUES clause to external query
                temp_string = "$to_be_replaced$"

        triple_patterns = self.get_triple_patterns()
        if triple_patterns != '':
            return ''.join([self.get_projection_string(),
                            " WHERE {\n",
                            temp_string,
                            triple_patterns,
                            "\n", "{\n" if self.subquery is not None else ''])
        else:
            return ''

    def get_selective(self):
        if self.include_selectivity and self.target_query is not None:
            target_node = get_target_node_statement(self.target_query)
            return ''.join([self.get_projection_string(),
                            " WHERE {\n",
                            target_node + ". {\n"])
        return ''

    def get_projection_string(self):
        return "SELECT DISTINCT " + \
               ", ".join(["?" + v for v in self.projected_variables])

    def get_triple_patterns(self):
        triple_string = "\n".join(self.triples)

        if len(self.filters) == 0:
            return triple_string

        return triple_string + self.generate_filter_string()

    def generate_filter_string(self):
        if len(self.filters) == 0:
            return ""

        return "\nFILTER(\n" + \
                (self.filters[0] if len(self.filters) == 1 else " AND\n".join(self.filters)) + \
               ")"

    def add_cardinality_filter(self, variables):
        for i in range(0, len(variables)):
            for j in range(i + 1, len(variables)):
                self.filters.append("?" + variables[i] + " != ?" + variables[j])

    def build_clause(self, c):
        variables = c.getVariables()

        if isinstance(c, Constraint):
            path = c.path

            if c.getValue() is not None:        # if there is a existing reference to another shape
                self.add_triple(path, c.getValue())
                return

            for v in variables:
                if c.getShapeRef() is not None and c.max == 0:
                    # constraint to target node of referenced shape
                    # e.g.: self.triples.append("?" + v + " a ub:" + c.getShapeRef() + ".")  # TODO
                    pass
                self.add_triple(path, "?" + v)

        if c.getValue() is not None:
            self.add_constant_filter(
                    variables.iterator().next(),
                    c.getValue().get(),
                    c.getIsPos()
            )

        if c.getDatatype() is not None:
            for v in variables:
                self.add_datatype_filter(v, c.getDatatype(), c.isPos())

        if len(variables) > 1:
            self.add_cardinality_filter(variables)

    def build_query(self, rule_pattern, include_prefixes):
        return Query(
                self.id,
                rule_pattern,
                self.get_SPARQL(include_prefixes, False)
        )
