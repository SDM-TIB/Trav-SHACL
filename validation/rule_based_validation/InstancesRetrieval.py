from validation.sparql.SPARQLEndpoint import SPARQLEndpoint
from validation.core.Literal import Literal
import time
import math
# from validation.rule_based_validation.utils.contactsource import contactSource
# from multiprocessing import Queue

class InstancesRetrieval:
    def __init__(self, endpoint_URL, shapes_dict, log_output, stats):
        self.endpointURL = endpoint_URL
        self.endpoint = SPARQLEndpoint(endpoint_URL)
        self.shapes_dict = shapes_dict
        self.log_output = log_output
        self.stats = stats

    def get_target_bindings(self, q):
        elem = q.get()
        while elem != 'EOF':
            yield elem['x']
            elem = q.get()

    def run_target_query(self, shape, query):
        if query is None:
            return []  # when a network has only some targets, a shape without a target class returns no new bindings
        self.log_output.write("\nEvaluating query:\n" + query)
        start = time.time() * 1000.0

        #queue = Queue()
        #contactSource(self.endpointURL, query, queue, 16384, 10000)
        #bindings = [b for b in self.get_target_bindings(queue)]

        bindings = self.endpoint.runQuery(
            shape.getId(),
            query,
            "JSON"
        )["results"]["bindings"]

        end = time.time() * 1000.0
        self.log_output.write("\nelapsed: " + str(end - start) + " ms\n")
        self.stats.recordQueryExecTime(end - start)
        self.stats.recordQuery()

        return bindings

    def extract_target_atoms(self, shape):
        '''

        :param shape:
        :return: set containing target literals
        '''
        query = shape.getTargetQuery()  # targetQuery is set in shape's definition file (json file)
        bindings = self.run_target_query(shape, query)
        shape.setRemainingTargetsCount(len(bindings))
        # NOTE: when using contactsource.py, the binding value has to be changed from 'b["x"]["value"]' to 'b'
        return {Literal(shape.getId(), b["x"]["value"], True) for b in bindings}  # target literals

    def get_instances_list(self, prev_eval_shape_name):
        '''
        Returns the valid and invalid instances of the previous evaluated shape (if there is one).
        :param prev_eval_shape_name: string containing the name of the shape of interest
        :return:
        '''
        if prev_eval_shape_name is None:
            return [], []
        return self.shapes_dict[prev_eval_shape_name].bindings, self.shapes_dict[prev_eval_shape_name].invalidBindings

    def get_formatted_instances(self, instances, separator, max_list_len):
        '''
        Depending on the number of instances that are going to be used for filtering the query,
        the function returns one or more lists with valid/invalid instances of previous shape
        in the corresponding format: using commas for instances contained in the VALUES clause or
        using spaces as separator for the instances in the FILTER NOT IN clause.

        :param instances: shortest instances list (either the one with valid or invalid targets)
        :param separator: string that contains either a comma or a space character.
        :param max_list_len: integer that sets the max number of instances in a query
        :return: list(s) containing all instances with the requested format
        '''
        chunks = len(instances) / max_list_len
        N = math.ceil(chunks)
        if chunks > 1:
            # Get split list
            listLen = math.ceil(len(instances) / N)
            shortestInstancesList = list(instances)
            splitLists = [shortestInstancesList[i:i + listLen] for i in range(0, len(shortestInstancesList), listLen)]

            return [separator.join(subList) for subList in splitLists]
        else:
            return [separator.join(instances)]

    def instantiate_filtered_target_query(self, shape, inst_type, prev_val_list, prev_inv_list, prev_eval_shape_name):
        '''
        Local variables:
            maxSplitNumber: heuristic of maximum possible number of instances considered for using filtering queries
                            instead of the initial target query (currently hard-coded to 256)
            maxInstancesPerQuery: number from which the list is going to start being split because of the max
                            number of characters allowed in a query

        :param shape:
        :param inst_type:
        :param prev_val_list:
        :param prev_inv_list:
        :param prev_eval_shape_name:
        :return: One or multiple queries depending on whether the instances list was split or not.
                 If the instances list was not split, the variable 'query' returns an array with one single query.
        '''
        self.log_output.write("\n" + inst_type + " instances shape: " + shape.id + " - child's (" + prev_eval_shape_name + ")")
        self.log_output.write(" instances: " + str(len(prev_val_list)) + " val " + str(len(prev_inv_list)) + " inv")
        targetQuery = shape.getTargetQuery()
        shortestList = prev_val_list if len(prev_val_list) < len(prev_inv_list) else prev_inv_list
        maxSplitNumber = 256
        maxInstancesPerQuery = 115

        if prev_val_list == prev_inv_list \
                or len(shortestList) > maxSplitNumber \
                or len(prev_val_list) == 0 or len(prev_inv_list) == 0:
            return [targetQuery]

        if (shortestList == prev_val_list and inst_type == "valid") \
                or (shortestList == prev_inv_list and inst_type == "invalid"):
            queryTemplate = shape.queriesWithVALUES[prev_eval_shape_name].getSparql()
            separator = " "
        else:
            queryTemplate = shape.queriesWithFILTER_NOT_IN[prev_eval_shape_name].getSparql()
            separator = ","

        formattedInstancesSplit = self.get_formatted_instances(shortestList, separator, maxInstancesPerQuery)
        return [queryTemplate.replace("$to_be_replaced$", sublist) for sublist in formattedInstancesSplit]

    def get_valid_targets(self, shape, inst_type, prev_val_list, prev_inv_list, prev_eval_shape_name):
        if len(prev_val_list) == 0:
            if len(prev_inv_list) > 0:
                shape.hasValidInstances = False
            return []
        else:
            query = self.instantiate_filtered_target_query(
                shape, inst_type, prev_val_list, prev_inv_list, prev_eval_shape_name)

            target_literals = set()
            for q in query:
                bindings = self.run_target_query(shape, q)
                # NOTE: when using contactsource.py, the binding value has to be changed from 'b["x"]["value"]' to 'b'
                target_literals.update([Literal(shape.getId(), b["x"]["value"], True) for b in bindings])
            return target_literals

    def get_invalid_targets(self, shape, inst_type, prev_val_list, prev_inv_list, prev_eval_shape_name):
        if len(prev_inv_list) == 0:
            return []
        else:
            query = self.instantiate_filtered_target_query(
                shape, inst_type, prev_val_list, prev_inv_list, prev_eval_shape_name)

            inv_target_literals = set()
            for idx, q in enumerate(query):
                bindings = self.run_target_query(shape, q)
                if idx == 0:  # update empty set
                    # NOTE: when using contactsource.py, change binding value from 'b["x"]["value"]' to 'b'
                    inv_target_literals.update([Literal(shape.getId(), b["x"]["value"], True) for b in bindings])
                else:
                    # NOTE: when using contactsource.py, change binding value from 'b["x"]["value"]' to 'b'
                    inv_target_literals.intersection([Literal(shape.getId(), b["x"]["value"], True) for b in bindings])

            return inv_target_literals

    def extract_target_atoms_with_filtering(self, shape, inst_type, prev_eval_shape_name):
        '''
        Run every time a new shape is going to be validated if it is connected to a shape
        that was already validated ("prevEvalShapeName") in order for the current shape to use queries
        filtered by those valid/invalid targets that correspond to the previous evaluated shape.

        The valid bindings obtained from the evaluation of the endpoint (target_literals) are added to the
        remaining targets (its validation is still pending).

        The bindings (inv_target_literals) retrieved after running the query which uses the invalid instances from
        previous shape evaluation as a filter, are directly set as invalid targets.

        :param shape: shape being evaluated
        :param inst_type:
        :param prev_eval_shape_name:
        :return:
        '''
        prev_val_list, prev_inv_list = self.get_instances_list(prev_eval_shape_name)

        target_literals = set()
        inv_target_literals = set()

        if inst_type == "valid" or inst_type == "all":
            target_literals = self.get_valid_targets(
                shape, "valid",   prev_val_list, prev_inv_list, prev_eval_shape_name)
        if inst_type == "violated" or inst_type == "all":
            inv_target_literals = self.get_invalid_targets(
                shape, "invalid", prev_val_list, prev_inv_list, prev_eval_shape_name)

        shape.setRemainingTargetsCount(len(target_literals))
        return target_literals, inv_target_literals

################################################

    def _get_constraint_bindings(self, q):
        elem = q.get()
        while elem != 'EOF':
            yield elem
            elem = q.get()

    def run_constraint_query(self, query_str, q):
        ''''
        Retrieve set of bindings from the SPARQL endpoint
        '''

        self.log_output.write("\n\nEvaluating query:\n" + query_str)
        start = time.time()*1000.0

        #queue = Queue()
        #contactSource(self.endpointURL, query_str, queue, 16384, 10000)
        #bindings = [b for b in self._get_constraint_bindings(queue)]

        bindings = self.endpoint.runQuery(
            q.getId(),
            query_str,
            "JSON"
        )["results"]["bindings"]

        end = time.time()*1000.0
        self.log_output.write("\nelapsed: " + str(end - start) + " ms\n")
        self.stats.recordQueryExecTime(end - start)

        self.log_output.write("\nNumber of solution mappings: " + str(len(bindings)) + "\n")
        self.stats.recordNumberOfSolutionMappings(len(bindings))
        self.stats.recordQuery()

        return bindings

    def filtering_constraint_query(self, shape, template_query, prev_val_list, prev_inv_list, prev_eval_shape_name,
                         maxSplitNumber, maxInstancesPerQuery, qType):
        if prev_eval_shape_name is not None \
                and len(prev_val_list) > 0 and len(prev_inv_list) > 0 \
                and len(prev_val_list) <= maxSplitNumber:
            VALUES_clauses = ""
            refPaths = "\n" if qType == "max" else ''
            formattedInstancesSplit = self.get_formatted_instances(prev_val_list, "", maxInstancesPerQuery)
            for c in shape.constraints:
                if c.shapeRef == prev_eval_shape_name:
                    var = " ?" + c.variables[0]
                    VALUES_clauses += "VALUES" + var + " {$instances$}\n"
                    if qType == "max":
                        focusVar = c.varGenerator.getFocusNodeVar()
                        refPaths += "?" + focusVar + " " + c.path + var + ".\n"

            return [template_query.replace("$to_be_replaced$",
                                           VALUES_clauses.replace("$instances$", sublist) + refPaths)
                    for sublist in formattedInstancesSplit]
        else:
            return [template_query.replace("$to_be_replaced$", "\n")]