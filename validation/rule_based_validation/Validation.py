# -*- coding: utf-8 -*-
__author__ = "Monica Figuera"

from validation.utils import fileManagement
from validation.utils.RuleBasedValidStats import RuleBasedValidStats
from validation.utils import SHACL2SPARQLEvalOrder
from validation.core.Literal import Literal
from validation.rule_based_validation.InstancesRetrieval import InstancesRetrieval
import time

class Validation:
    def __init__(self, endpoint_URL, node_order, shapes_dict, option, target_shape_predicates, selectivity_enabled,
                       use_SHACL2SPARQL_order, log_output, valid_output, invalid_output, stats_output, traces_output):

        if use_SHACL2SPARQL_order:
            dataset = 'LUBM'
            self.node_order = SHACL2SPARQLEvalOrder.get_node_order(dataset, len(shapes_dict))
        else:
            self.node_order = node_order

        self.shapes_dict = shapes_dict
        self.eval_inst_type = option  # possible values: 'valid', 'violated', 'all'
        self.target_shape_predicates = target_shape_predicates
        self.selectivity_enabled = selectivity_enabled  # use selective queries

        self.log_output = log_output
        self.valid_output = valid_output
        self.violated_output = invalid_output
        self.stats_output = stats_output
        self.stats = RuleBasedValidStats()

        self.log_output.write("Node order: " + str(self.node_order) + '\n')
        self.traces_output = traces_output
        self.start_of_verification = time.time() * 1000.0
        self.traces_output.write("Target, #TripleInThatClass, TimeSinceStartOfVerification(ms)\n")

        self.inst_retrieval = InstancesRetrieval(endpoint_URL, shapes_dict, self.log_output, self.stats)

    def write_targets_to_file(self, state):
        """
        Saves to local file the new validated target

        :param state:
        :return:
        """
        if self.eval_inst_type == "valid" or self.eval_inst_type == "all":
            for valid in state.valid_targets:
                self.valid_output.write(valid)

        if self.eval_inst_type == "violated" or self.eval_inst_type == "all":
            for invalid in state.invalid_targets:
                self.violated_output.write(invalid)

        for trace in state.traces:
            self.traces_output.write(trace)

    def exec(self):
        focus_shape = self.shapes_dict[self.node_order.pop(0)]  # first shape to be evaluated
        depth = 0  # evaluation order
        initial_targets = self.inst_retrieval.extract_target_atoms(focus_shape)

        self.log_output.write("Retrieving (initial) targets ...")
        self.log_output.write("\nTargets retrieved.")
        self.log_output.write("\nNumber of targets:\n" + str(len(initial_targets)))
        self.stats.recordInitialTargets(str(len(initial_targets)))
        start = time.time() * 1000.0
        state = EvalState(initial_targets, self.shapes_dict)
        self.validate(
            state,
            depth,
            focus_shape
        )
        finish = time.time() * 1000.0
        elapsed = round(finish - start)
        self.stats.recordTotalTime(elapsed)
        print("Total execution time: ", str(elapsed), " ms")
        self.log_output.write("\nMaximal (initial) number or rules in memory: " + str(self.stats.maxRuleNumber))
        self.write_targets_to_file(state)
        self.stats.writeAll(self.stats_output)

        fileManagement.closeFile(self.valid_output)
        fileManagement.closeFile(self.violated_output)
        fileManagement.closeFile(self.stats_output)
        fileManagement.closeFile(self.log_output)

    def is_satisfiable(self, a, state, shape_name):
        atom_in_eval_preds = a.getPredicate() in state.evaluated_predicates
        is_rule_head = False
        is_inferred = False
        atom = a.getAtom()
        if state.atoms[shape_name]["pendingAtoms"].get(atom) is not None:
            is_rule_head = state.atoms[shape_name]["pendingAtoms"][atom]["isRuleHead"]
        elif state.atoms[shape_name]["inferredAtoms"].get(atom) is not None:
            is_rule_head = state.atoms[shape_name]["inferredAtoms"][atom]["isRuleHead"]
            is_inferred = True

        return not atom_in_eval_preds or is_rule_head or is_inferred

    def register_target(self, t, is_valid, depth, log_message, focus_shape, state):
        """
        Adds each target to the set of valid/invalid instances of the focus shape,
        adds targets to sets that contain the logs that will be saved to local files containing the classified targets

        :param t: target
        :param is_valid: boolean value that tells if 't' is a valid or a violated instance
        :param depth: current level (shape) in the evaluation order / number of shapes evaluated so far
        :param log_message:
        :param focus_shape: shape that contains the target 't'
        :param state:
        """
        f_shape_str = ", focus shape " + focus_shape.id if focus_shape is not None else ""
        log = t.getStr() + ", depth " + str(depth) + f_shape_str + ", " + log_message + "\n"

        instance = "<" + t.getArg() + ">"

        if is_valid:
            self.shapes_dict[t.getPredicate()].bindings.add(instance)
            state.valid_targets.add(log)
        else:
            self.shapes_dict[t.getPredicate()].invalidBindings.add(instance)
            state.invalid_targets.add(log)

        target_type = "valid" if is_valid else "violated"
        trace_log = target_type + ", " + \
                    str(state.traces_count) + ", " + \
                    str(round(time.time() * 1000.0 - self.start_of_verification)) + "\n"

        state.traces.add(trace_log)
        state.traces_count += 1

    def ground_and_saturate(self, bindings, state, focus_shape, query_RP, shape_RP):
        """
        Rules given by
          - query rule pattern (of the current evaluated constraint query)
          - and shape rule pattern (shape for which the constraint query was evaluated)
        are going to be grounded (instantiated) with instances retrieved from the endpoint.

        Repeat steps (1), (2), (3) for each of the two rule patterns:
        # step (1) - derive negative information:
                For any (possibly negated) atom 'a', we verify if it is not satisfiable
                => infer the negation of the atom
        # step (2) - infer rule:
                If the negation of any rule body has already been inferred
                => the rule cannot be satisfied, we don't add it to ruleMap, and infer the negation of the rule head
        # step (3) - add pending rule to ruleMap for future classification / infer rule head (if candidate valid target):

        :param bindings: list of instances retrieved from the endpoint
        :param state:
        :param focus_shape:
        :param query_RP: query rule pattern
        :param shape_RP: shape rule pattern
        :return:
        """
        shape_name = focus_shape.getId()
        remaining_fshape_targets = focus_shape.getRemainingTargetsCount()

        query_RP_head = query_RP.getHead()
        qH_pred = query_RP_head.getPredicate()
        qH_arg = query_RP_head.getArg()
        qH_isPositive = query_RP_head.getIsPos()
        query_RP_body = query_RP.getBody()

        shape_RP_head = shape_RP.getHead()
        sH_pred = shape_RP_head.getPredicate()
        sH_arg = shape_RP_head.getArg()
        sH_is_positive = shape_RP_head.getIsPos()
        shape_RP_body = shape_RP.getBody()

        start = time.time() * 1000.0

        for binding in bindings:
            query_rule_head = Literal(qH_pred, binding[qH_arg]["value"], qH_isPositive)
            shape_rule_head = Literal(sH_pred, binding[sH_arg]["value"], sH_is_positive)
            sH_is_candidate_valid_target = sH_pred in self.target_shape_predicates and shape_rule_head in state.remaining_targets

            # INFER case (2) -> target already classified as invalid
            if state.atoms[shape_name]["inferredAtoms"].get(query_rule_head.getNegation()) is not None:
                continue

            body = set()
            is_all_body_inferred = True
            negated_body = False
            for a_RP in query_RP_body:
                atom_pred = a_RP.getPredicate()  # query body predicates always contain a shape name
                atom_shape_name = atom_pred.split("_")[0]
                a = Literal(atom_pred, binding[a_RP.getArg()]["value"], a_RP.getIsPos())
                body.add(a)
                if state.atoms[atom_pred]["inferredAtoms"].get(a) is None:                   # if item not inferred yet
                    # step (1) - negate (unmatchable body atoms)
                    if not self.is_satisfiable(a, state, atom_shape_name):
                        negated_atom = a.getNegation() if a.getIsPos() else a                # eg, !Department_d1_max...
                        state.atoms[atom_pred]["inferredAtoms"][negated_atom] = {"isRuleHead": False}
                        negated_body = True
                    else:
                        is_all_body_inferred = False     # we infer when a body atom is not satisfiable

                    # step (2) - infer negation of rule head (from negation of rule body atom)
                    if state.atoms[atom_pred]["inferredAtoms"].get(a.getNegation()) is not None:
                        is_all_body_inferred = False
                        negated_body = True
                        state.atoms[shape_name]["inferredAtoms"][query_rule_head.getNegation()] = {"isRuleHead": False}
                        break  # negated body atom means the rule cannot be inferred -> halt the loop (short-circuit)

            # step (3) - add pending rule / infer rule head
            if negated_body:
                if sH_is_candidate_valid_target:
                    self.register_target(shape_rule_head, False, "collection (negated body)", "", focus_shape, state)
                    state.remaining_targets.discard(shape_rule_head)
                    remaining_fshape_targets -= 1
                state.atoms[shape_name]["inferredAtoms"][shape_rule_head.getNegation()] = {"isRuleHead": False}
                continue

            if not is_all_body_inferred:
                state.add_shape_rule(state.atoms[shape_name]["ruleMap"], query_rule_head, frozenset(body))
                state.atoms[shape_name]["pendingAtoms"][query_rule_head] = {"isRuleHead": True}
            else:
                state.atoms[shape_name]["inferredAtoms"][query_rule_head] = {"isRuleHead": True}  # infer rule head

            # Shape Rule Pattern #
            if state.atoms[shape_name]["inferredAtoms"].get(shape_rule_head) is not None \
               or state.atoms[shape_name]["inferredAtoms"].get(shape_rule_head.getNegation()) is not None:
                continue

            body = set()
            is_all_body_inferred = True
            negated_body = False
            for atom_RP in shape_RP_body:
                atom_pred = atom_RP.getPredicate()
                atom_shape_name = atom_pred.split("_")[0]  # shape name of the current body atom
                a = Literal(atom_pred, binding[atom_RP.getArg()]["value"], atom_RP.getIsPos())
                body.add(a)
                if state.atoms[shape_name]["inferredAtoms"].get(a) is None:
                    # step (1) - negate
                    if state.atoms[shape_name]["pendingAtoms"].get(a) is not None:
                        if not self.is_satisfiable(a, state, atom_shape_name):
                            negated_atom = a.getNegation() if a.getIsPos() else a
                            state.atoms[atom_shape_name]["inferredAtoms"][negated_atom] = {"isRuleHead": False}
                            negated_body = True
                        else:
                            is_all_body_inferred = False

                    # step (2) - infer
                    if state.atoms[atom_shape_name]["inferredAtoms"].get(a.getNegation()) is not None:
                        negated_body = True
                        is_all_body_inferred = False
                        state.atoms[shape_name]["inferredAtoms"][shape_rule_head.getNegation()] = {"isRuleHead": False}
                        break

            # step (3) - add pending rule / infer
            if negated_body:
                if sH_is_candidate_valid_target:
                    self.register_target(shape_rule_head, False, "collection", "", focus_shape, state)
                    state.remaining_targets.discard(shape_rule_head)
                    remaining_fshape_targets -= 1
                state.atoms[shape_name]["inferredAtoms"][shape_rule_head.getNegation()] = {"isRuleHead": False}
                continue

            if not is_all_body_inferred:
                state.add_shape_rule(state.atoms[shape_name]["ruleMap"], shape_rule_head, frozenset(body))
                state.atoms[shape_name]["pendingAtoms"][shape_rule_head] = {"isRuleHead": True}
            else:
                if sH_is_candidate_valid_target:
                    self.register_target(shape_rule_head, True, "collection", "", focus_shape, state)
                    state.remaining_targets.discard(shape_rule_head)
                    remaining_fshape_targets -= 1
                state.atoms[shape_name]["inferredAtoms"][shape_rule_head] = {"isRuleHead": True}

        end = time.time() * 1000.0

        focus_shape.setRemainingTargetsCount(remaining_fshape_targets)
        self.stats.recordGroundingTime(end - start)
        self.log_output.write("\nGrounding rules ... \nelapsed: " + str(end - start) + " ms\n")

    def negate_unmatchable_heads(self, state, depth, shape, ruleMap):
        """
        This procedure derives negative information
        For any (possibly negated) atom 'a' that is either a target or appears in some rule, we
        may be able to infer that 'a' cannot hold:
          if 'a' is not inferred yet,
          if the query has already been evaluated,
          and if there is not rule with 'a' as its head.
        Thus, in such case, 'not a' is added to the inferredAtoms list of state.atoms.

        :param state:
        :param depth: current level (shape) in the evaluation order / number of shapes evaluated so far
        :param shape: current shape being evaluated
        :param ruleMap:
        :return:
        """
        all_body_atoms = set(frozenset().union(*set().union(*ruleMap.values())))
        new_negated_atom_found = False
        for a in all_body_atoms:
            atom_pred = a.getPredicate()
            atom_shape_name = atom_pred.split("_")[0]  # e.g., Department_d1_pos -> Department
            shape_name = shape.getId()
            if not self.is_satisfiable(a, state, shape_name):
                negated_atom = a.getNegation() if a.getIsPos() else a  # e.g., !Department_d1_max_...
                if state.atoms[atom_shape_name]["inferredAtoms"].get(negated_atom) is None:
                    new_negated_atom_found = True
                    state.atoms[atom_shape_name]["inferredAtoms"][negated_atom] = {"isRuleHead": False}

        remaining = set()
        for t in state.remaining_targets:
            if not self.is_satisfiable(t, state, t.getPredicate()):
                self.register_target(t, False, depth, "", shape, state)
                state.atoms[t.getPredicate()]["inferredAtoms"][t.getNegation()] = {"isRuleHead": False}
            else:
                remaining.add(t)

        state.remaining_targets = remaining

        return new_negated_atom_found

    def apply_rules(self, state, depth, shape, ruleMap):
        """
        INFER procedure performs 2 types of inferences:
        # case (1): If the set of rules contains a rule and each of the rule bodies has already been inferred
                    => head of the rule is inferred, rule dropped.
        # case (2): If the negation of any rule body has already been inferred
                    => this rule cannot be applied (rule head not inferred) so the entire rule is dropped.

        :param state:
        :param depth: current level (shape) in the evaluation order / number of shapes evaluated so far
        :param shape: current shape being evaluated
        :param ruleMap:
        :return:
        """
        fresh_literals = False
        ruleMap_copy = ruleMap.copy()
        for head in ruleMap_copy:
            bodies = ruleMap[head]
            head_shape_name = head.getPredicate().split("_")[0]
            for body in bodies:
                is_all_body_inferred = True
                for a in body:
                    atom_shape_name = a.getPredicate().split("_")[0]
                    if state.atoms[atom_shape_name]["inferredAtoms"].get(a) is None:
                        is_all_body_inferred = False

                        # case (2)
                        if state.atoms[atom_shape_name]["inferredAtoms"].get(a.getNegation()) is not None:
                            if head in state.remaining_targets:
                                self.register_target(head, False, depth, "", shape, state)
                                state.remaining_targets.discard(head)

                            state.atoms[head_shape_name]["inferredAtoms"][head.getNegation()] = {"isRuleHead": False}

                            if ruleMap.get(head) is not None:
                                del ruleMap[head]
                            break
                # case (1)
                if is_all_body_inferred:
                    fresh_literals = True

                    if head in state.remaining_targets:
                        self.register_target(head, True, depth, "", shape, state)
                        state.remaining_targets.discard(head)

                    # e.g., University(...), University_d1_pos(...)
                    state.atoms[head_shape_name]["inferredAtoms"][head] = {"isRuleHead": True}

                    if ruleMap.get(head) is not None:
                        del ruleMap[head]
                    break

        if not fresh_literals:
            return False

        self.log_output.write("\nRemaining targets: " + str(len(state.remaining_targets)))
        return True

    def saturate_remaining(self, state, depth, shape):
        """
        The saturation process consists of two steps:
        1. Negate: same as in step (1) of procedure ground_and_saturate(...)
        2. Infer: same is step (2) of procedure ground_and_saturate(...)
        Repeat 1 and 2 until no further changes are made (i.e., no new inferences found)

        :param state:
        :param depth: current level (shape) in the evaluation order / number of shapes evaluated so far
        :param shape: current shape being evaluated
        """
        for parent in state.atoms[shape.getId()]["parentShapes"]:
            if len(state.atoms[parent]["pendingChildrenShapes"]) == 0:
                ruleMap = state.atoms[parent]["ruleMap"]

                negated = self.negate_unmatchable_heads(state, depth, shape, ruleMap)
                inferred = self.apply_rules(state, depth, shape, ruleMap)
                if negated or inferred:
                    self.saturate_remaining(state, depth, shape)
                else:
                    self.saturate_remaining(state, depth, self.shapes_dict[parent])

    def eval_constraints_queries(self, shape, prev_eval_shape_name, state):
        """
        We skip evaluation of target query (short-circuit operation) if all the targets of a shape were already
        violated in the interleaving (ground and saturate(...)) process

        :param shape:
        :param prev_eval_shape_name:
        :param state:
        """
        prev_val_list, prev_inv_list = self.inst_retrieval.get_instances_list(prev_eval_shape_name)
        maxSplitNumber = shape.maxSplitSize
        maxInstancesPerQuery = 80

        # There is a single min query per shape
        filtered_min_query = self.inst_retrieval.filtering_constraint_query(
                        shape, shape.minQuery.getSparql(), prev_val_list, prev_inv_list, prev_eval_shape_name,
                        maxSplitNumber, maxInstancesPerQuery, "min")
        for queryStr in filtered_min_query:
            self.ground_and_saturate(self.inst_retrieval.run_constraint_query(queryStr, shape.minQuery),
                                     state, shape, shape.minQuery.getRulePattern(), shape.getRulePatterns()[0])

        # There might be several max queries per shape
        # Evaluate only if the current shape still has targets to be validated
        if shape.getId() in self.target_shape_predicates and shape.getRemainingTargetsCount() > 0:
            for q in shape.maxQueries:
                filtered_max_query = self.inst_retrieval.filtering_constraint_query(
                            shape, q.getSparql(), prev_val_list, prev_inv_list, prev_eval_shape_name,
                            maxSplitNumber, maxInstancesPerQuery, "max")
                for queryStr in filtered_max_query:
                    self.ground_and_saturate(self.inst_retrieval.run_constraint_query(queryStr, q),
                                             state, shape, q.getRulePattern(), shape.getRulePatterns()[0])

    def eval_shape(self, state, depth, shape):
        """
        Validates the focus shape by performing a saturation process.

        Saturation only occurs if the current shape is connected in the network as a parent to a shape that was already
        evaluated and has any valid instance. This is,
            if the child node in the network (previously evaluated shape) contains only invalid instances, then
            all retrieved instances of the shape being currently evaluated were already registered as invalid
            so there is no need to further validate min/max constraints.

        :param state:
        :param depth: current level (shape) in the evaluation order / number of shapes evaluated so far
        :param shape: current shape being evaluated
        """
        self.log_output.write("\nEvaluating queries for shape " + shape.getId())

        if shape.hasValidInstances:
            self.eval_constraints_queries(shape, state.prev_eval_shape_name, state)
            state.evaluated_predicates.update(shape.getPredicates())
            for parent in state.atoms[shape.getId()]["parentShapes"]:
                state.atoms[parent]["pendingChildrenShapes"].discard(shape.getId())
            self.log_output.write("\nStarting saturation ...")
            startS = time.time() * 1000.0

            if not state.atoms[shape.getId()]["saturationDone"]:
                ready_to_saturate = True
                children_shapes = state.atoms[shape.getId()]["pendingChildrenShapes"]
                if len(children_shapes) > 0:
                    for child in children_shapes:
                        if not state.atoms[child]["saturationDone"]:
                            ready_to_saturate = False

                if ready_to_saturate:
                    self.saturate_remaining(state, depth, shape)
                    state.atoms[shape.getId()]["saturationDone"] = True

            endS = time.time() * 1000.0
            self.stats.recordSaturationTime(endS - startS)
            self.log_output.write("\nsaturation ...\nelapsed: " + str(endS - startS) + " ms")
        else:
            self.log_output.write("\nNo saturation for shape ..." + shape.getId())

        state.add_visited_shape(shape)

        self.log_output.write("\n\nValid targets: " + str(len(state.valid_targets)))
        self.log_output.write("\nInvalid targets: " + str(len(state.invalid_targets)))
        self.log_output.write("\nRemaining targets: " + str(len(state.remaining_targets)))

    def get_eval_child_name(self, shape, visited_shapes):
        """
        (possibly) Returns the name of a shape that was already evaluated, if it is connected as a child in the network
        to the shape that is currently being validated, and contains relevant information for query filtering purposes:
            - the number of valid or invalid instances is less than a threshold (now threshold is set as 256),
            - the list of invalid targets from the child's shape in the network is not empty,
            - there was a target query assigned for this "child" shape (also called "previous evaluated shape").

        :param shape: current shape being evaluated
        :param visited_shapes:
        :return: string with the (best) previously evaluated shape name or None if no shape fulfills the conditions
        """
        best_ref = None
        best_val_threshold = 256
        best_inv_threshold = 256
        for prev_shape in visited_shapes:
            prev_shape_name = prev_shape.getId()
            if shape.referencedShapes.get(prev_shape_name) is not None:
                len_val = len(prev_shape.bindings)
                len_inv = len(prev_shape.invalidBindings)

                if (0 < len_val < best_val_threshold) or (0 < len_inv < best_inv_threshold):
                    if len_inv > 0 and prev_shape.getTargetQuery() is not None:
                        best_ref = prev_shape_name
        # print("BEST:", best_ref)
        return best_ref

    def retrieve_next_targets(self, state, depth, next_focus_shape):
        """
        There are two possible queries for retrieving targets:
           - w/o filtering: retrieve instances belonging to a certain target class,
           - with filtering: if 'selective queries: true' parameter is enabled, ask for instances that belong to the
                             shape's target class and additionally filter retrieving instances based on targets
                             retrieved by an evaluated referenced shape (prev_eval_shape_name).
        :param state:
        :param depth:
        :param next_focus_shape:
        :return:
        """
        next_focus_shape_name = next_focus_shape.getId()

        self.log_output.write("\n\n****************************************\n********************************")
        self.log_output.write("\nRetrieving (next) targets ...")

        if self.selectivity_enabled:
            state.prev_eval_shape_name = self.get_eval_child_name(next_focus_shape, state.visited_shapes)

            if state.prev_eval_shape_name is not None:
                # get instances based on results from evaluated child referenced by the current shape
                val_targets, inv_targets = self.inst_retrieval.extract_target_atoms_with_filtering(
                    next_focus_shape, self.eval_inst_type, state.prev_eval_shape_name)

                # invalid targets are classified straight away (not considered for further saturation)
                for t in inv_targets:
                    self.register_target(t, False, depth, "", next_focus_shape, state)
                    state.atoms[next_focus_shape_name]["inferredAtoms"][t.getNegation()] = {"isRuleHead": False}

                # valid targets are added to the set of remaining targets
                state.remaining_targets.update(val_targets)
            else:
                next_targets = self.inst_retrieval.extract_target_atoms(next_focus_shape)
                state.remaining_targets.update(next_targets)
        else:
            next_targets = self.inst_retrieval.extract_target_atoms(next_focus_shape)
            state.remaining_targets.update(next_targets)

    def validate(self, state, depth, focus_shape):
        """
        This procedure performs the following:
        1. Starts remaining saturation of current focus shape (procedure eval_shape(...))
        2. Gets the next shape over which evaluation will be performed.
        3. Retrieves the target instances of the next shape to be evaluated.

        :param state:
        :param depth: current level (shape) in the evaluation order / number of shapes evaluated so far
        :param focus_shape: current shape being evaluated
        :return:
        """
        # termination condition: all shapes have been visited
        if len(state.visited_shapes) == len(self.shapes_dict):
            if self.eval_inst_type == "violated" or self.eval_inst_type == "all":
                for t in state.remaining_targets:
                    self.register_target(t, False, depth, "not violated after termination", None, state)
            return

        self.log_output.write("\n\n********************************")
        self.log_output.write("\nStarting validation at depth: " + str(depth))

        self.eval_shape(state, depth, focus_shape)  # validate current selected shape

        # select next shape to be evaluated from the already defined list with the evaluation order
        next_focus_shape = None
        if len(self.node_order) > 0:  # if there are more shapes to be evaluated
            next_focus_shape = self.shapes_dict[self.node_order.pop(0)]
            if next_focus_shape.getTargetQuery() is not None:
                self.retrieve_next_targets(state, depth, next_focus_shape)

        self.validate(state, depth + 1, next_focus_shape)


class EvalState:
    def __init__(self, target_literals, shapes_dict):
        self.atoms = {}
        for shape_name in shapes_dict:
            self.atoms[shape_name] = \
                               {"parentShapes": set(),
                                "pendingChildrenShapes": set(shapes_dict[shape_name].referencedShapes.keys()),
                                "saturationDone": False,
                                "pendingAtoms": {},
                                "inferredAtoms": {},
                                "ruleMap": {}
                               }
        for shape_name in shapes_dict:
            child_shapes = shapes_dict[shape_name].referencedShapes
            for child in child_shapes:
                self.atoms[child]["parentShapes"].add(shape_name)

        self.remaining_targets = target_literals
        self.visited_shapes = set()
        self.evaluated_predicates = set()
        self.prev_eval_shape_name = None
        self.valid_targets = set()
        self.invalid_targets = set()
        self.traces = set()
        self.traces_count = 0

    def add_visited_shape(self, s):
        self.visited_shapes.add(s)

    def add_shape_rule(self, map, head, body):
        if map.get(head) is None:
            s = set()
            s.add(body)
            map[head] = s
        else:
            map[head].add(body)
