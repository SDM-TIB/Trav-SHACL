# -*- coding: utf-8 -*-
__author__ = 'Monica Figuera'

import math
import time

from SPARQLWrapper import SPARQLWrapper

from TravSHACL.sparql.SPARQLEndpoint import SPARQLEndpoint
from TravSHACL.sparql.QueryGenerator import get_target_node_statement
from TravSHACL.constraints.MinOnlyConstraint import MinOnlyConstraint
from TravSHACL.constraints.MaxOnlyConstraint import MaxOnlyConstraint


class InstancesRetrieval:
    """This class is responsible for retrieving the instances from a SPARQL endpoint."""

    def __init__(self, endpoint:  SPARQLEndpoint, shapes_dict, stats):
        """
        Creates a new instance for the data retrieval.

        :param endpoint: SPARQL endpoint to collect the data from
        :param shapes_dict: a Python dictionary holding all shapes of the shape schema
        :param stats: instance of ValidationStats to keep the statistics up-to-date
        """
        self.endpoint = endpoint
        self.shapes_dict = shapes_dict
        self.stats = stats

    def run_constraint_query(self, q, query_str):
        """
        Retrieves answers from the SPARQL endpoint.

        :param q: Query object representing the SPARQL query to answer
        :param query_str: possibly rewritten query string, e.g., a partition of the original query
        :return: answer set bindings for the constraint query
        """
        self.stats.update_log(''.join(['\n\nEvaluating query ', q.get_id(), ':\n', query_str]))

        start = time.time()*1000.0
        bindings = self.endpoint.run_query(query_str)['results']['bindings']
        end = time.time()*1000.0

        self.stats.update_log(''.join(['\nelapsed: ', str(end - start), ' ms\n']))
        self.stats.record_query_exec_time(end - start)
        self.stats.record_query()
        self.stats.update_log(''.join(['\nNumber of solution mappings: ', str(len(bindings)), '\n']))
        self.stats.record_number_of_sol_mappings(len(bindings))
        return bindings

    def execute_sparql_constraint(self, constraint_id, query_str, instance_list):
        """
        Retrieves all the violations of a SPARQL constraint from the endpoint.

        :param constraint_id: the ID of the SPARQL constraint
        :param query_str: the SPARQL query belonging to the constraint represented as a string
        :param instance_list: a list with the instances for which the constraint needs to be checked
        :return: list of all instances violating the constraint, i.e., the SPARQL query result is not empty
        """
        self.stats.update_log(''.join(['\n\nEvaluating query for ', constraint_id, ':\n', query_str]))

        violations = []
        start = time.time() * 1000.0
        for instance in instance_list:
            query = query_str.replace('$this', '<' + instance + '>')
            if len(self.endpoint.run_query(query)['results']['bindings']) > 0:
                violations.append(instance)
        end = time.time() * 1000.0

        self.stats.update_log(''.join(['\nelapsed: ', str(end - start), ' ms\n']))
        self.stats.record_query_exec_time(end - start)
        self.stats.record_query()
        self.stats.update_log(''.join(['\nNumber of solution mappings: ', str(len(violations)), '\n']))
        self.stats.record_number_of_sol_mappings(len(violations))

        return violations

    def extract_targets(self, shape):
        """
        Retrieves answers from the SPARQL endpoint.
        When a network of shapes has only 'some' targets, a shape without a target class returns no new bindings

        :param shape: focus shape being evaluated
        :return: set containing target literals (stored in the form of built-in python tuples)
        """
        query = shape.get_target_query()  # targetQuery is set in shape's definition file (json file)
        self.stats.update_log(''.join(['\nEvaluating target query for ', shape.id, ':\n', query]))

        start = time.time() * 1000.0
        bindings = self.endpoint.run_query(query)['results']['bindings']
        end = time.time() * 1000.0

        self.stats.update_log('\nelapsed: ' + str(end - start) + ' ms\n')
        self.stats.record_query_exec_time(end - start)
        self.stats.record_query()
        self.stats.update_log('\nNumber of targets retrieved: ' + str(len(bindings)))
        return {(shape.id, b['x']['value'], True) for b in bindings}

    def extract_options(self, shape):
        """
        Retrieves answers from the SPARQL endpoint.
        When a network of shapes has only 'some' targets, a shape without a target class returns no new bindings

        :param shape: focus shape being evaluated
        :return: set containing target literals (stored in the form of built-in python tuples)
        """
        query = shape.get_or_query()  # or_query is formed in the shape class
        if not query:
            return
        self.stats.update_log(''.join(['\nEvaluating OR_options query for ', shape.id, ':\n', query]))
        start = time.time() * 1000.0
        bindings = self.endpoint.run_query(query)['results']['bindings']
        end = time.time() * 1000.0

        self.stats.update_log('\nelapsed: ' + str(end - start) + ' ms\n')
        self.stats.record_query_exec_time(end - start)
        self.stats.record_query()
        self.stats.update_log('\nNumber of options retrieved: ' + str(len(bindings)))
        return {(shape.id, b['x']['value'], True) for b in bindings}

    def extract_targets_with_filter(self, shape, filtering_shape):
        """
        Retrieves more selective query answers by separating early invalidated targets from the still pending ones.

        :param shape: focus shape being evaluated
        :param filtering_shape: referenced shape used to filter query, or None
        :return: two sets containing all targets of 'shape': pending targets to validate and directly invalidated targets
        """
        if self.endpoint.get_endpoint_type() != SPARQLWrapper:
            return self.extract_targets(shape), []  # FIXME: rdflib cannot handle unbound variables in aggregates, hence, no filtering will be applied

        # Valid and invalid instances of the previous evaluated shape (if any)
        prev_val_list = set() if filtering_shape is None else filtering_shape.get_valid_targets()
        prev_inv_list = set() if filtering_shape is None else filtering_shape.get_invalid_targets()
        pending_targets = set()
        inv_targets = set()

        self.stats.update_log(''.join(['\n', 'instances retrieval ', shape.get_id(),
                              ": [out-neighbor's (", filtering_shape.get_id(), ')']))
        self.stats.update_log(''.join([' instances: ', str(len(prev_val_list)), ' valid ',
                              str(len(prev_inv_list)), ' invalid]']))

        max_split_number = 256
        max_instances_per_query = 115
        shortest_inst_list = prev_val_list if len(prev_val_list) < len(prev_inv_list) else prev_inv_list

        if prev_val_list == prev_inv_list or \
                len(prev_val_list) == 0 or len(prev_inv_list) == 0 or \
                len(shortest_inst_list) > max_split_number:
            pending_targets = self.extract_targets(shape)
            return pending_targets, inv_targets

        query_template = shape.queriesFilters[filtering_shape.get_id()]
        constraint = query_template['constraint']
        query_template = query_template['query_valid'].get_sparql() if shortest_inst_list == prev_val_list else query_template['query_invalid'].get_sparql()
        separator = ' '

        split_instances = self.__get_formatted_instances(shortest_inst_list, separator, max_instances_per_query)
        query = [query_template.replace('$instances_to_add$', sublist) for sublist in split_instances]

        start = time.time() * 1000.0
        for q in query:
            self.stats.update_log('\nEvaluating target query for ' + shape.id + ':\n' + q)
            bindings = self.endpoint.run_query(q)['results']['bindings']
            for b in bindings:
                instance = b['x']['value']
                cardinality = int(b['cnt']['value'])

                if isinstance(constraint, MinOnlyConstraint):
                    if cardinality < constraint.min:
                        inv_targets.update([(shape.id, instance, True)])
                    else:
                        pending_targets.update([(shape.id, instance, True)])
                elif isinstance(constraint, MaxOnlyConstraint):
                    if cardinality > constraint.max:
                        inv_targets.update([(shape.id, instance, True)])
                    else:
                        pending_targets.update([(shape.id, instance, True)])
        end = time.time() * 1000.0
        self.stats.record_query_exec_time(end - start)
        self.stats.record_query()
        self.stats.update_log('\nelapsed: ' + str(end - start) + ' ms\n')
        self.stats.update_log('\nNumber of pending targets: ' + str(len(pending_targets)))
        self.stats.update_log('\nNumber of invalid targets: ' + str(len(inv_targets)))
        return pending_targets, inv_targets

    def rewrite_constraint_query(self, shape, q, filtering_shape, q_type, use_selective_queries):
        """
        Filters constraint query with targets from 'filtering_shape' (if any).
        The end-user can restrict number of instances allowed for considering a filtering clause.
        Since the length of a query string is restricted by the SPARQL endpoint configuration, the query might be
        divided into several sub-queries, where each subquery contains at most 'max_instances_per_query' (set to 80).

        :param shape: focus shape being evaluated
        :param q: Query object representing the target query of the focus shape
        :param filtering_shape: shape used to filter the instances of the target query
        :param q_type: query type
        :param use_selective_queries: boolean that indicates if the selective validation is enabled
        :return: list with (possibly partitioned) filtered query or original query if no filter was applied
        """
        max_split_number = shape.get_query_split_threshold()
        max_instances_per_query = 80
        prev_val_list = set() if filtering_shape is None else filtering_shape.get_valid_targets()
        prev_inv_list = set() if filtering_shape is None else filtering_shape.get_invalid_targets()
        query_template = q.get_sparql()

        if use_selective_queries and '$inter_shape_type_to_add$' in query_template:
            for var, inter_shape_name in q.get_inter_shape_refs_names().items():
                inter_shape = self.shapes_dict[inter_shape_name]
                inter_shape_triple = ''
                if inter_shape.targetType == 'class':
                    inter_shape_triple = get_target_node_statement(inter_shape.targetQueryNoPref).replace('?x', '?' + var)
                    if inter_shape_triple[-1] != '}':
                        inter_shape_triple += '.'
                query_template = query_template.replace('$inter_shape_type_to_add$', inter_shape_triple)
        else:
            query_template = query_template.replace('$inter_shape_type_to_add$', '')

        if use_selective_queries and \
                filtering_shape is not None and \
                len(prev_val_list) > 0 and len(prev_inv_list) > 0 and \
                len(prev_val_list) <= max_split_number:
            values_clauses = ''
            inter_shape_triples = '\n'
            separator = ''
            split_instances = self.__get_formatted_instances(prev_val_list, separator, max_instances_per_query)
            for c in shape.constraints:
                if c.shapeRef == filtering_shape.get_id() and c.min == 1:
                    obj_var = ' ?' + c.variables[0]
                    values_clauses += 'VALUES' + obj_var + ' {$instances$}\n'
                    if q_type == 'max':
                        focus_var = c.varGenerator.get_focus_node_var()
                        inter_shape_triples += '?' + focus_var + ' ' + c.path + obj_var + '.\n'

            return [query_template.replace(
                        '$filter_clause_to_add$',
                        values_clauses.replace('$instances$', sublist) + inter_shape_triples
                    ) for sublist in split_instances]

        return [query_template.replace('$filter_clause_to_add$', '')]

    @staticmethod
    def __get_formatted_instances(instances, separator, max_list_len):
        """
        Takes instances to be added to the query's filtering clause and returns one or more lists with (in)valid
        instances in two possible formats: (a) using commas for instances in the VALUES clause or (b) using
        spaces as separator for the instances in the FILTER NOT IN clause.

        :param instances: shortest instances list (either the one with valid or invalid targets)
        :param separator: string that contains either a comma or a space character
        :param max_list_len: integer that sets the max number of instances in a query
        :return: set containing all instances with the requested format
        """
        chunks = len(instances) / max_list_len
        n = math.ceil(chunks)
        if chunks > 1:  # Get split list
            instances = tuple(instances)
            inst_count = math.ceil(len(instances) / n)
            split_lists = {instances[i:i + inst_count] for i in range(0, inst_count, inst_count)}
            return {separator.join(subList) for subList in split_lists}
        return {separator.join(instances)}
