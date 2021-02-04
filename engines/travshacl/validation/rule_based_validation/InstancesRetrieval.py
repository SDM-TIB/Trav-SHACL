# -*- coding: utf-8 -*-
__author__ = "Monica Figuera"

from validation.sparql.SPARQLEndpoint import SPARQLEndpoint
import time
import math


class InstancesRetrieval:
    def __init__(self, endpoint_URL, shapes_dict, stats):
        self.endpointURL = endpoint_URL
        self.endpoint = SPARQLEndpoint(endpoint_URL)
        self.shapes_dict = shapes_dict
        self.stats = stats

    def run_constraint_query(self, q, query_str):
        """
        Retrieves answers from the SPARQL endpoint.
        """
        self.stats.updateValidationLog(''.join(["\n\nEvaluating query:\n", query_str]))

        start = time.time()*1000.0
        bindings = self.endpoint.runQuery(q.getId(), query_str, "JSON")["results"]["bindings"]
        end = time.time()*1000.0

        self.stats.updateValidationLog(''.join(["\nelapsed: ", str(end - start), " ms\n"]))
        self.stats.recordQueryExecTime(end - start)
        self.stats.recordQuery()
        self.stats.updateValidationLog(''.join(["\nNumber of solution mappings: ", str(len(bindings)), "\n"]))
        self.stats.recordNumberOfSolutionMappings(len(bindings))
        return bindings

    def extract_targets(self, shape):
        """
        Retrieves answers from the SPARQL endpoint.
        When a network of shapes has only "some" targets, a shape without a target class returns no new bindings

        :return: set containing target literals (stored in the form of built-in python tuples)
        """
        query = shape.getTargetQuery()  # targetQuery is set in shape's definition file (json file)
        self.stats.updateValidationLog(''.join(["\nEvaluating target query:\n", query]))

        start = time.time() * 1000.0
        bindings = self.endpoint.runQuery(shape.id, query, "JSON")["results"]["bindings"]
        end = time.time() * 1000.0

        self.stats.updateValidationLog("\nelapsed: " + str(end - start) + " ms\n")
        self.stats.recordQueryExecTime(end - start)
        self.stats.recordQuery()
        self.stats.updateValidationLog("\nNumber of targets retrieved: " + str(len(bindings)))
        return {(shape.id, b["x"]["value"], True) for b in bindings}

    def extract_targets_with_filter(self, shape, inst_type, prev_eval_shape_name):
        """
        Runs when 'shape' is referencing 'prev_eval_shape_name' and 'shape' can get its targets by running queries
        filtered with the (in)valid targets that belong to the previously evaluated shape.

        :param shape: shape being evaluated
        :param inst_type: string containing "valid", "violated" or "all"
        :param prev_eval_shape_name: string containing the name of the referenced shape used to filter query or None
        :return: two sets containing the targets of shape: pending targets to validate and directly invalidated targets
        """
        # Valid and invalid instances of the previous evaluated shape (if any)
        prev_val_list = set() if prev_eval_shape_name is None else self.shapes_dict[prev_eval_shape_name].getValidTargets()
        prev_inv_list = set() if prev_eval_shape_name is None else self.shapes_dict[prev_eval_shape_name].getInvalidTargets()

        pending_targets, inv_targets = set(), set()
        if inst_type == "valid" or inst_type == "all":
            pending_targets = self._get_pending_targets(shape, prev_val_list, prev_inv_list, prev_eval_shape_name)
            self.stats.updateValidationLog(''.join(["\nNumber of targets retrieved: ", str(len(pending_targets))]))
        if inst_type == "violated" or inst_type == "all":
            inv_targets = self._get_invalid_targets(shape, prev_val_list, prev_inv_list, prev_eval_shape_name)
            self.stats.updateValidationLog(''.join(["\nNumber of targets retrieved: ", str(len(inv_targets))]))

        return pending_targets, inv_targets

    def _get_pending_targets(self, shape, prev_val_list, prev_inv_list, prev_eval_shape_name):
        if len(prev_val_list) == 0:
            return set()

        query = self._filter_target_query(shape, "valid", prev_val_list, prev_inv_list, prev_eval_shape_name)
        pending_targets = set()
        start = time.time() * 1000.0
        for q in query:
            self.stats.updateValidationLog("\nEvaluating target query:\n" + q)
            bindings = self.endpoint.runQuery(shape.id, q, "JSON")["results"]["bindings"]
            pending_targets.update([(shape.id, b["x"]["value"], True) for b in bindings])
        end = time.time() * 1000.0
        self.stats.recordQueryExecTime(end - start)
        self.stats.recordQuery()
        return pending_targets

    def _get_invalid_targets(self, shape, prev_val_list, prev_inv_list, prev_eval_shape_name):
        if len(prev_inv_list) == 0:
            return set()

        query = self._filter_target_query(shape, "violated", prev_val_list, prev_inv_list, prev_eval_shape_name)
        inv_targets = set()
        start = time.time() * 1000.0
        for idx, q in enumerate(query):
            self.stats.updateValidationLog("\nEvaluating target query:\n" + q)
            bindings = self.endpoint.runQuery(shape.id, q, "JSON")["results"]["bindings"]
            if idx == 0:  # update empty set
                inv_targets.update([(shape.id, b["x"]["value"], True) for b in bindings])
            else:
                inv_targets.intersection([(shape.id, b["x"]["value"], True) for b in bindings])
        end = time.time() * 1000.0
        self.stats.recordQueryExecTime(end - start)
        self.stats.recordQuery()
        return inv_targets

    def _filter_target_query(self, shape, inst_type, prev_val_list, prev_inv_list, prev_eval_shape_name):
        """
        Gets query template for valid (VALUES) and invalid (FILTER NOT IN) instances of current 'shape' and instantiates
        the $to_be_replaced$ part with the actual instances given by the previous evaluated shape's list of instances.

        Local variables:
            max_split_number: heuristic of maximum possible number of instances considered for using filtering queries
                            instead of the initial target query (currently hard-coded to 256)
            max_instances_per_query: number from which the list is going to start being split because of the max
                            number of characters allowed in a SPARQL endpoint's query

        :return: One or multiple queries depending on whether the instances list was split or not.
                 If the instances list was not split, the variable 'query' returns an array with one single query.
        """
        self.stats.updateValidationLog(''.join(["\n", inst_type, " instances shape: ", shape.id,
                                                " - child's (", prev_eval_shape_name, ")"]))
        self.stats.updateValidationLog(''.join([" instances: ",
                                                str(len(prev_val_list)), " val ",
                                                str(len(prev_inv_list)), " inv"]))
        max_split_number = 256
        max_instances_per_query = 115
        shortest_inst_list = prev_val_list if len(prev_val_list) < len(prev_inv_list) else prev_inv_list

        if prev_val_list == prev_inv_list or \
                len(prev_val_list) == 0 or len(prev_inv_list) == 0 or \
                len(shortest_inst_list) > max_split_number:
            return [shape.getTargetQuery()]

        if (shortest_inst_list == prev_val_list and inst_type == "valid") \
                or (shortest_inst_list == prev_inv_list and inst_type == "violated"):
            query_template = shape.queriesWithVALUES[prev_eval_shape_name].getSparql()
            separator = " "
        else:
            query_template = shape.queriesWithFILTER_NOT_IN[prev_eval_shape_name].getSparql()
            separator = ","

        split_instances = self._get_formatted_instances(shortest_inst_list, separator, max_instances_per_query)
        return [query_template.replace("$to_be_replaced$", sublist) for sublist in split_instances]

    def filter_constraint_query(self, shape, query_template, prev_eval_shape_name, q_type):
        """
        Filters constraint query with targets from 'prev_eval_shape_name'. Since the length of a query string is
        restricted by the SPARQL endpoint configuration, the query might be divided into several sub-queries,
        where each subquery contains at most 'max_inst_per_query' (set to 80) instances.

        :return: list with (possibly split) filtered query or original query if no filter could be applied
        """
        max_split_number = shape.maxSplitSize
        max_instances_per_query = 80
        prev_val_list = set() if prev_eval_shape_name is None else self.shapes_dict[prev_eval_shape_name].getValidTargets()
        prev_inv_list = set() if prev_eval_shape_name is None else self.shapes_dict[prev_eval_shape_name].getInvalidTargets()

        if prev_eval_shape_name is not None and \
                len(prev_val_list) > 0 and len(prev_inv_list) > 0 and \
                len(prev_val_list) <= max_split_number:
            VALUES_clauses = ""
            ref_paths = "\n" if q_type == "max" else ''
            split_instances = self._get_formatted_instances(prev_val_list, "", max_instances_per_query)
            for c in shape.constraints:
                if c.shapeRef == prev_eval_shape_name:
                    var = " ?" + c.variables[0]
                    VALUES_clauses += "VALUES" + var + " {$instances$}\n"
                    if q_type == "max":
                        focus_var = c.varGenerator.getFocusNodeVar()
                        ref_paths += "?" + focus_var + " " + c.path + var + ".\n"

            return [query_template.replace("$to_be_replaced$", VALUES_clauses.replace("$instances$", sublist) + ref_paths)
                    for sublist in split_instances]

        return [query_template.replace("$to_be_replaced$", "\n")]

    @staticmethod
    def _get_formatted_instances(instances, separator, max_list_len):
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
        N = math.ceil(chunks)
        if chunks > 1:  # Get split list
            inst_count = math.ceil(len(instances) / N)
            split_lists = {instances[i:i + inst_count] for i in range(0, inst_count, inst_count)}
            return {separator.join(subList) for subList in split_lists}
        return {separator.join(instances)}
