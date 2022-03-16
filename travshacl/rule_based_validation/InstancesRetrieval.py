# -*- coding: utf-8 -*-
__author__ = "Monica Figuera"

import math
import time

from travshacl.sparql.SPARQLEndpoint import SPARQLEndpoint
from travshacl.sparql.QueryGenerator import get_target_node_statement


class InstancesRetrieval:
    """This class is responsible for retrieving the instances from a SPARQL endpoint."""

    def __init__(self, endpoint_url, shapes_dict, stats):
        """
        Creates a new instance for the data retrieval.

        :param endpoint_url: URL of the SPARQL endpoint to collect the data from
        :param shapes_dict: a Python dictionary holding all shapes of the shape schema
        :param stats: instance of ValidationStats to keep the statistics up-to-date
        """
        self.endpointURL = endpoint_url
        self.endpoint = SPARQLEndpoint(endpoint_url)
        self.shapes_dict = shapes_dict
        self.stats = stats

    def run_constraint_query(self, q, query_str):
        """
        Retrieves answers from the SPARQL endpoint.

        :param q: Query object representing the SPARQL query to answer
        :param query_str: possibly rewritten query string, e.g., a partition of the original query
        :return: answer set bindings for the constraint query
        """
        self.stats.update_log(''.join(["\n\nEvaluating query ", q.get_id(), ":\n", query_str]))

        start = time.time()*1000.0
        bindings = self.endpoint.run_query(query_str)["results"]["bindings"]
        end = time.time()*1000.0

        self.stats.update_log(''.join(["\nelapsed: ", str(end - start), " ms\n"]))
        self.stats.record_query_exec_time(end - start)
        self.stats.record_query()
        self.stats.update_log(''.join(["\nNumber of solution mappings: ", str(len(bindings)), "\n"]))
        self.stats.record_number_of_sol_mappings(len(bindings))
        return bindings

    def extract_targets(self, shape):
        """
        Retrieves answers from the SPARQL endpoint.
        When a network of shapes has only "some" targets, a shape without a target class returns no new bindings

        :param shape: focus shape being evaluated
        :return: set containing target literals (stored in the form of built-in python tuples)
        """
        query = shape.get_target_query()  # targetQuery is set in shape's definition file (json file)
        self.stats.update_log(''.join(["\nEvaluating target query for ", shape.id, ":\n", query]))

        start = time.time() * 1000.0
        bindings = self.endpoint.run_query(query)["results"]["bindings"]
        end = time.time() * 1000.0

        self.stats.update_log("\nelapsed: " + str(end - start) + " ms\n")
        self.stats.record_query_exec_time(end - start)
        self.stats.record_query()
        self.stats.update_log("\nNumber of targets retrieved: " + str(len(bindings)))
        return {(shape.id, b["x"]["value"], True) for b in bindings}

    def extract_targets_with_filter(self, shape, filtering_shape):
        """
        Retrieves more selective query answers by separating early invalidated targets from the still pending ones.

        :param shape: focus shape being evaluated
        :param filtering_shape: referenced shape used to filter query, or None
        :return: two sets containing all targets of 'shape': pending targets to validate and directly invalidated targets
        """
        # Valid and invalid instances of the previous evaluated shape (if any)
        prev_val_list = set() if filtering_shape is None else filtering_shape.get_valid_targets()
        prev_inv_list = set() if filtering_shape is None else filtering_shape.get_invalid_targets()

        pending_targets = self.__get_pending_targets(shape, prev_val_list, prev_inv_list, filtering_shape)
        self.stats.update_log(''.join(["\nNumber of targets retrieved: ", str(len(pending_targets))]))

        inv_targets = self.__get_invalid_targets(shape, prev_val_list, prev_inv_list, filtering_shape)
        self.stats.update_log(''.join(["\nNumber of targets retrieved: ", str(len(inv_targets))]))

        return pending_targets, inv_targets

    def __get_pending_targets(self, shape, prev_val_list, prev_inv_list, filtering_shape):
        """
        Retrieves all targets of the current 'shape' based on the result of a previously evaluated neighbor
        for which the validation status has still to be determined, i.e., they are pending.

        :param shape: focus shape being evaluated
        :param prev_val_list: list of valid instances from neighboring shape
        :param prev_inv_list: list of invalid instances from neighboring shape
        :param filtering_shape: previously evaluated neighboring shape
        :return: bindings for all pending targets based on the previously evaluated instances
        """
        if len(prev_val_list) == 0:
            return set()

        query = self.__filter_target_query(shape, prev_val_list, prev_inv_list, filtering_shape, "pending")
        pending_targets = set()
        start = time.time() * 1000.0
        for q in query:
            self.stats.update_log("\nEvaluating target query for " + shape.id + ":\n" + q)
            bindings = self.endpoint.run_query(q)["results"]["bindings"]
            pending_targets.update([(shape.id, b["x"]["value"], True) for b in bindings])
        end = time.time() * 1000.0
        self.stats.record_query_exec_time(end - start)
        self.stats.record_query()
        return pending_targets

    def __get_invalid_targets(self, shape, prev_val_list, prev_inv_list, filtering_shape):
        """
        Retrieves all invalid targets of current 'shape' based on the result of a previously evaluated neighbor.

        :param shape: focus shape being evaluated
        :param prev_val_list: list of valid instances from neighboring shape
        :param prev_inv_list: list of invalid instances from neighboring shape
        :param filtering_shape: previously evaluated neighboring shape
        :return: bindings for all invalid targets based on the previously evaluated instances
        """
        if len(prev_inv_list) == 0:
            return set()

        query = self.__filter_target_query(shape, prev_val_list, prev_inv_list, filtering_shape, "violated")
        inv_targets = set()
        start = time.time() * 1000.0
        for idx, q in enumerate(query):
            self.stats.update_log("\nEvaluating target query for " + shape.id + ":\n" + q)
            bindings = self.endpoint.run_query(q)["results"]["bindings"]
            if idx == 0:  # update empty set
                inv_targets.update([(shape.id, b["x"]["value"], True) for b in bindings])
            else:
                inv_targets.intersection([(shape.id, b["x"]["value"], True) for b in bindings])
        end = time.time() * 1000.0
        self.stats.record_query_exec_time(end - start)
        self.stats.record_query()
        return inv_targets

    def __filter_target_query(self, shape, prev_val_list, prev_inv_list, filtering_shape, inst_type):
        """
        Gets query template for valid (VALUES) and invalid (FILTER NOT IN) instances of current 'shape' and
        instantiates the $instances_to_add$ string with the actual instances given by the evaluated neighbor
        shape's list of instances.

        Local variables:
            max_split_number: heuristic of maximum possible number of instances considered for using filtering queries
                            instead of the initial target query (currently hard-coded to 256)
            max_instances_per_query: number from which the list is going to start being split because of the max
                            number of characters allowed in a SPARQL endpoint's query

        :param shape: focus shape being evaluated
        :param prev_val_list: list of valid instances from neighboring shape
        :param prev_inv_list: list of invalid instances from neighboring shape
        :param filtering_shape: previously evaluated neighboring shape
        :param inst_type: string indicating the type of instances to retrieve ("pending" or "violated")
        :return: One or multiple queries depending on whether the instances list was split or not.
                 If the instances list was not split, the variable 'query' returns an array with one single query.
        """
        self.stats.update_log(''.join(["\n", inst_type, " instances retrieval ", shape.get_id(),
                              ": [out-neighbor's (", filtering_shape.get_id(), ")"]))
        self.stats.update_log(''.join([" instances: ", str(len(prev_val_list)), " valid ",
                                       str(len(prev_inv_list)), " invalid]"]))
        max_split_number = 256
        max_instances_per_query = 115
        shortest_inst_list = prev_val_list if len(prev_val_list) < len(prev_inv_list) else prev_inv_list

        if prev_val_list == prev_inv_list or \
                len(prev_val_list) == 0 or len(prev_inv_list) == 0 or \
                len(shortest_inst_list) > max_split_number:
            return [shape.get_target_query()]

        if (shortest_inst_list == prev_val_list and inst_type == "pending") \
            or (shortest_inst_list == prev_inv_list and inst_type == "violated"):
            query_template = shape.queriesWithVALUES[filtering_shape.get_id()].get_sparql()
        else:
            query_template = shape.queriesWithFILTER_NOT_IN[filtering_shape.get_id()].get_sparql()

        separator = " "
        split_instances = self.__get_formatted_instances(shortest_inst_list, separator, max_instances_per_query)
        return [query_template.replace("$instances_to_add$", sublist) for sublist in split_instances]

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

        if use_selective_queries and "$inter_shape_type_to_add$" in query_template:
            for var, inter_shape_name in q.get_inter_shape_refs_names().items():
                inter_shape = self.shapes_dict[inter_shape_name]
                inter_shape_triple = ''
                if inter_shape.targetType == 'class':
                    inter_shape_triple = get_target_node_statement(inter_shape.targetQueryNoPref).replace('?x', '?' + var)
                    if inter_shape_triple[-1] != '}':
                        inter_shape_triple += '.'
                query_template = query_template.replace("$inter_shape_type_to_add$", inter_shape_triple)
        else:
            query_template = query_template.replace("$inter_shape_type_to_add$", "")

        if use_selective_queries and \
                filtering_shape is not None and \
                len(prev_val_list) > 0 and len(prev_inv_list) > 0 and \
                len(prev_val_list) <= max_split_number:
            values_clauses = ""
            inter_shape_triples = "\n"
            separator = ""
            split_instances = self.__get_formatted_instances(prev_val_list, separator, max_instances_per_query)
            for c in shape.constraints:
                if c.shapeRef == filtering_shape.get_id() and c.min == 1:
                    obj_var = " ?" + c.variables[0]
                    values_clauses += "VALUES" + obj_var + " {$instances$}\n"
                    if q_type == "max":
                        focus_var = c.varGenerator.get_focus_node_var()
                        inter_shape_triples += "?" + focus_var + " " + c.path + obj_var + ".\n"

            return [query_template.replace("$filter_clause_to_add$",
                                           values_clauses.replace("$instances$", sublist) + inter_shape_triples)
                    for sublist in split_instances]

        return [query_template.replace("$filter_clause_to_add$", "")]

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
