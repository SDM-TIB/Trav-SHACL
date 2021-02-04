# -*- coding: utf-8 -*-
__author__ = "Monica Figuera"

from validation.utils import fileManagement
from validation.utils.ValidationStats import ValidationStats
from validation.utils import SHACL2SPARQLEvalOrder
from validation.rule_based_validation.InstancesRetrieval import InstancesRetrieval
import time


class Validation:
    def __init__(self, endpoint_URL, node_order, shapes_dict, option, target_shape_predicates, use_selective_queries,
                       use_SHACL2SPARQL_order, output_dir_name, save_stats, save_targets_to_file):

        self.node_order = node_order if not use_SHACL2SPARQL_order \
                                     else SHACL2SPARQLEvalOrder.get_node_order("LUBM", len(shapes_dict))
        self.shapes_dict = shapes_dict
        self.eval_type = option  # possible values: "valid", "violated", "all"
        self.target_shape_predicates = target_shape_predicates
        self.selectivity_enabled = use_selective_queries

        self.output_dir_name = output_dir_name
        self.save_stats = save_stats
        self.save_targets_to_file = save_targets_to_file
        self.stats = ValidationStats()
        self.traces = set()

        self.stats.updateValidationLog("Node order: " + str(self.node_order) + '\n')
        self.InstRetrieval = InstancesRetrieval(endpoint_URL, shapes_dict, self.stats)
        self.valid_targets_after_termination = set()
        self.start_of_verification = time.time() * 1000.0

    def exec(self):
        focus_shape = self.shapes_dict[self.node_order.pop(0)]
        state = ValidationState(self.shapes_dict)
        initial_targets = self.retrieve_next_targets(state, focus_shape, state.shapes_state)
        state.remaining_targets.update(initial_targets)
        state.shapes_state[focus_shape.getId()]['remaining_targets_count'] = len(initial_targets)

        start = time.time() * 1000.0
        self.validate(state, focus_shape)
        finish = time.time() * 1000.0
        elapsed = round(finish - start)
        self.stats.recordTotalTime(elapsed)
        print("Total execution time: ", str(elapsed), " ms")
        self.stats.updateValidationLog("\n\nTotal number of rules: " + str(self.stats.totalSolutionMappings*2))
        self.stats.updateValidationLog("\nMaximal number or rules in memory: " + str(self.stats.maxSolutionMappings*2))
        return self.validation_output(state.shapes_state)

    def validate(self, state, focus_shape):
        if len(state.visited_shapes) == len(self.shapes_dict):
            if self.eval_type == "valid" or self.eval_type == "all":
                self.valid_targets_after_termination.update(state.remaining_targets)
            return

        self.stats.updateValidationLog("\n\n>>>>> Starting validation of shape: " + focus_shape.getId())
        state.evaluated_predicates.add(focus_shape.getId())
        self.eval_shape(state, focus_shape, state.shapes_state)

        next_focus_shape = None
        if len(self.node_order) > 0:
            next_focus_shape = self.shapes_dict[self.node_order.pop(0)]
            pending_targets = self.retrieve_next_targets(state, next_focus_shape, state.shapes_state)
            state.remaining_targets.update(pending_targets)

        self.validate(state, next_focus_shape)

    def eval_shape(self, state, shape, shapes_state):
        """
        Starts evaluation of focus shape (interleave + saturation). After interleaving process, the focus shape can
        continue validating its remaining targets when all its referenced shapes were already validated.
        """
        shape_name = shape.getId()
        if shapes_state[shape_name]['remaining_targets_count'] > 0:
            self.eval_constraints_queries(state, shape, state.prev_eval_shape_name)  # interleave

            self.stats.updateValidationLog("\nStarting saturation ...")
            start = time.time() * 1000.0
            if shapes_state[shape_name]['pending_refs_to_saturate'] == 0:  # ready to saturate
                self.saturate_remaining(state, shape_name, shape_name, shapes_state)
            end = time.time() * 1000.0

            self.stats.recordSaturationTime(end - start)
            self.stats.updateValidationLog("\nsaturation ...\nelapsed: " + str(end - start) + " ms")
        else:
            self.stats.updateValidationLog("\nNo further saturation for shape " + shape_name)

        state.visited_shapes.add(shape)
        self.stats.updateValidationLog("\nRemaining targets: " + str(len(state.remaining_targets)))

    def eval_constraints_queries(self, state, shape, filter_ref_shape_name):
        """
        Evaluates all constraints queries of focus shape 'shape'.
        Skips evaluation of remaining queries if all the targets of a shape were already violated during interleaving.
        Per shape, there is one query with all min constraints (unless partitioned) and one query per max constraint.

        :param state: state of the validation
        :param shape: focus shape
        :param filter_ref_shape_name: name of a shape referenced by 'shape' which provides filtering instances
        """
        shape_name = shape.getId()
        shape_rp = shape.getRulePatterns()[0]

        min_query_rp = shape.minQuery.getRulePattern()
        skip_q = self.eval_constraints_query(state, shape, shape.minQuery, filter_ref_shape_name, min_query_rp, shape_rp, "min")

        for q in shape.maxQueries:
            if q.getId() not in skip_q \
               and shape_name in self.target_shape_predicates \
               and state.shapes_state[shape_name]['remaining_targets_count'] > 0:
                max_query_rp = q.getRulePattern()
                self.eval_constraints_query(state, shape, q, filter_ref_shape_name, max_query_rp, shape_rp, "max")

    def saturate_remaining(self, state, shape_name, shape_invalidating_name, shapes_state):
        """
        The saturation process consists of two steps:
        1. Negate: same as in step (1) of interleaving process
        2. Infer: same is step (2) of interleaving process
        Repeat 1 and 2 until no further changes are made (i.e., no new inferences found)

        :param state: current state of the validation
        :param shape_name: name of focus shape or its "parents" (after recursion)
        :param shape_invalidating_name: name of the shape that started the saturation before recursion
        :param shapes_state: current validation's state of each shape
        """
        rule_map = shapes_state[shape_name]['rule_map']
        negated = self.negate_unmatchable_heads(state, rule_map, shape_invalidating_name, state.evaluated_predicates, shapes_state, state.preds_to_shapes)
        inferred = self.apply_rules(state.remaining_targets, rule_map, shape_invalidating_name, shapes_state, state.preds_to_shapes)
        if negated or inferred:
            self.saturate_remaining(state, shape_name, shape_invalidating_name, shapes_state)
        else:
            for parent_name in self.shapes_dict[shape_name].getParentShapes():
                shapes_state[parent_name]['pending_refs_to_saturate'] -= 1
                if shapes_state[parent_name]['pending_refs_to_saturate'] == 0 \
                   and shapes_state[parent_name]['remaining_targets_count'] > 0:
                    self.saturate_remaining(state, parent_name, shape_invalidating_name, shapes_state)

    def negate_unmatchable_heads(self, state, rule_map, shape_invalidating_name, evaluated_predicates, shapes_state, preds_to_shapes):
        """
        Derives negation of atoms that are not satisfiable. An atom 'a' is not satisfiable when:
        its query (predicate of 'a') was already evaluated, no rule has 'a' as its head, and 'a' is not inferred yet.

        :param state: current state of the validation
        :param rule_map: set of rules associated to focus shape or any of its parents
        :param shape_invalidating_name: name of the shape that started the saturation before recursion
        :param evaluated_predicates: target/min/max query predicates evaluated so far
        :return: True if new unsatisfied rule head literals were found, False otherwise
        """
        new_negated_atom_found = False
        all_body_atoms = set(frozenset().union(*set().union(*rule_map.values())))
        for a in all_body_atoms:
            a_state = shapes_state[preds_to_shapes[a[0]]]  # atom's shape state (e.g., Dept_d1_pos -> Dept)
            if a[0] in evaluated_predicates \
               and (a[0], a[1], True) not in a_state['rule_map'] \
               and (a[0], a[1], True) not in a_state['inferred']:  # if atom 'a' is not satisfiable
                negated_atom = (a[0], a[1], False)
                if negated_atom not in a_state['inferred']:
                    new_negated_atom_found = True
                    a_state['inferred'].add(negated_atom)

        remaining = set()
        for a in state.remaining_targets:
            t_state = shapes_state[a[0]]  # target's shape state
            if a[0] in evaluated_predicates \
               and (a[0], a[1], True) not in t_state['rule_map'] \
               and (a[0], a[1], True) not in t_state['inferred']:  # if atom 'a' is not satisfiable
                self.register_target(a, "violated", shape_invalidating_name, shapes_state)
                t_state['inferred'].add((a[0], a[1], not a[2]))
                t_state['remaining_targets_count'] -= 1
            else:
                remaining.add(a)
        state.remaining_targets = remaining
        return new_negated_atom_found

    def apply_rules(self, remaining_targets, rule_map, shape_invalidating_name, shapes_state, preds_to_shapes):
        """
        Performs two types of inferences:
        # case (1): If the rule map contains a rule and some of its bodies was already inferred
                    => head of the rule is inferred, rule dropped.
        # case (2): If the negation of any rule body was already inferred
                    => the rule cannot be applied (rule head not inferred), rule dropped.

        :param rule_map: set of rules associated to focus shape or any of its parents
        :param shape_invalidating_name: name of the shape that started the saturation before recursion
        :return: True if new inferences were found, False otherwise
        """
        fresh_literals = False
        rule_map_copy = rule_map.copy()
        for head, bodies in rule_map_copy.items():
            head_shape_name = preds_to_shapes[head[0]]
            inferred_bodies = {"F" if (a[0], a[1], False) in shapes_state[preds_to_shapes[a[0]]]['inferred']
                                   else ("T" if a in shapes_state[preds_to_shapes[a[0]]]['inferred']
                                       else "P") for body in bodies for a in body}
            if 'T' in inferred_bodies:  # case (1)
                fresh_literals = True
                if head in remaining_targets:
                    self.register_target(head, "valid", shape_invalidating_name, shapes_state)
                    remaining_targets.discard(head)
                    shapes_state[head_shape_name]['remaining_targets_count'] -= 1
                shapes_state[head_shape_name]['inferred'].add(head)
                del rule_map[head]
            elif 'F' in inferred_bodies:  # case (2)
                if head in remaining_targets:
                    self.register_target(head, "violated", shape_invalidating_name, shapes_state)
                    remaining_targets.discard(head)
                    shapes_state[head_shape_name]['remaining_targets_count'] -= 1
                shapes_state[head_shape_name]['inferred'].add((head[0], head[1], not head[2]))
                del rule_map[head]

        if not fresh_literals:
            return False
        self.stats.updateValidationLog("\nRemaining targets: " + str(len(remaining_targets)))
        return True

    def eval_constraints_query(self, state, shape, q, filter_ref_shape_name, q_rule_pattern, s_rule_pattern, q_type):
        """
        Evaluates corresponding min/max query of 'shape' and starts interleaving process for all answers retrieved.

        The focus shape applies knowledge gained from the validated referenced shape 'filter_ref_shape_name'. The query
        'q' is rewritten to include a filter (VALUES clause) containing the targets of 'filter_ref_shape_name'.

        :param state: current state of the validation
        :param shape: focus shape
        :param q: query to be evaluated
        :param filter_ref_shape_name: name of a shape referenced by 'shape' which provides filtering instances
        :param q_rule_pattern: query rule pattern
        :param s_rule_pattern: shape rule pattern
        :param q_type: query type ("min" or "max")
        :return:
        """
        shapes_state = state.shapes_state
        preds_to_shapes = state.preds_to_shapes
        shape_name = shape.getId()
        query_rp_head = q_rule_pattern.getHead()
        shape_rp_head = s_rule_pattern.getHead()
        query_rp_body = q_rule_pattern.getBody()
        shape_rp_body = s_rule_pattern.getBody()

        focus_shape_state = shapes_state[shape_name]
        remaining_targets = state.remaining_targets

        q_body_eval_pred = [pattern[0] in state.evaluated_predicates for pattern in query_rp_body]
        s_body_eval_pred = [pattern[0] in state.evaluated_predicates for pattern in shape_rp_body]
        q_body_ref_shapes = [preds_to_shapes[pattern[0]] for pattern in query_rp_body]
        s_body_ref_shapes = [preds_to_shapes[pattern[0]] for pattern in shape_rp_body]

        shape_max_refs, skip_q = self.get_max_refs(shape, state.evaluated_predicates)
        inter_constr_count = {}

        for query_str in self.InstRetrieval.filter_constraint_query(shape, q.getSparql(), filter_ref_shape_name, q_type):
            start = time.time() * 1000.0
            for b in self.InstRetrieval.run_constraint_query(q, query_str):
                q_head = (query_rp_head[0], b[query_rp_head[1]]["value"], query_rp_head[2])
                s_head = (shape_rp_head[0], b[shape_rp_head[1]]["value"], shape_rp_head[2])

                body = set()
                is_body_inferred = True
                negated_body = False
                for i, atom_pattern in enumerate(query_rp_body):
                    atom_shape_state = shapes_state[q_body_ref_shapes[i]]
                    a = (atom_pattern[0], b[atom_pattern[1]]["value"], atom_pattern[2])
                    body.add(a)
                    if a not in atom_shape_state['inferred']:
                        if (a[0], a[1], not a[2]) not in focus_shape_state['inferred'] and q_body_eval_pred[i]:
                            continue

                        # step (1) - negate (unmatchable body atoms)
                        if q_body_eval_pred[i] \
                           and (a[0], a[1], True) not in focus_shape_state['rule_map'] \
                           and (a[0], a[1], True) not in focus_shape_state['inferred']:  # a not satisf
                            atom_shape_state['inferred'].add((a[0], a[1], False))

                            # step (2) - infer negation of rule head (negated body atom)
                            negated_body = True
                            break  # if at least one negated body atom, the rule cannot be inferred -> halt the loop
                        else:
                            is_body_inferred = False
                    ##########
                    elif q_type == "min" and shape_max_refs.get(q_body_ref_shapes[i]) is not None:
                        if inter_constr_count.get(s_head) is None:
                            inter_constr_count[s_head] = {inter_constraint: set() for inter_constraint in shape_max_refs}
                        inter_constr_count[s_head][q_body_ref_shapes[i]].add(a)
                        if len(inter_constr_count[s_head][q_body_ref_shapes[i]]) > shape_max_refs[q_body_ref_shapes[i]]:
                            negated_body = True
                    ##########

                if negated_body:
                    focus_shape_state['inferred'].add((q_head[0], q_head[1], False))
                    if s_head[2] and s_head in remaining_targets:
                        self.register_target(s_head, "violated", shape_name, shapes_state)
                        state.remaining_targets.discard(s_head)
                        focus_shape_state['remaining_targets_count'] -= 1
                    continue

                # step (3) - add pending rule / add inferred query head
                if not is_body_inferred:
                    if q_head not in focus_shape_state['rule_map']:
                        s = set()
                        s.add(frozenset(body))
                        focus_shape_state['rule_map'][q_head] = s
                    else:
                        focus_shape_state['rule_map'][q_head].add(frozenset(body))
                else:
                    focus_shape_state['inferred'].add(q_head)

                # Shape rule pattern #
                body = set()
                is_body_inferred = True
                negated_body = False
                for i, atom_pattern in enumerate(shape_rp_body):
                    atom_shape_state = shapes_state[s_body_ref_shapes[i]]
                    a = (atom_pattern[0], b[atom_pattern[1]]["value"], atom_pattern[2])
                    body.add(a)
                    if a not in atom_shape_state['inferred']:
                        if (a[0], a[1], not a[2]) not in focus_shape_state['inferred'] and s_body_eval_pred[i]:
                            continue

                        # step (1) - negate (unmatchable body atoms)
                        elif s_body_eval_pred[i] \
                            and (a[0], a[1], True) not in focus_shape_state['rule_map'] \
                                and (a[0], a[1], True) not in focus_shape_state['inferred']:

                            atom_shape_state['inferred'].add((a[0], a[1], False))

                            # step (2) - infer negation of rule head (negated body atom)
                            focus_shape_state['inferred'].add((s_head[0], s_head[1], not s_head[2]))
                            if s_head[2] and s_head in remaining_targets:
                                self.register_target(s_head, "violated", shape_name, shapes_state)
                                state.remaining_targets.discard(s_head)
                                focus_shape_state['remaining_targets_count'] -= 1
                                negated_body = True
                            break
                        else:
                            is_body_inferred = False

                if negated_body:
                    continue

                # step (3) - add pending rule / classify valid target (all body inferred)
                if not is_body_inferred:
                    if s_head not in focus_shape_state['rule_map']:
                        s = set()
                        s.add(frozenset(body))
                        focus_shape_state['rule_map'][s_head] = s
                    else:
                        focus_shape_state['rule_map'][s_head].add(frozenset(body))
                else:
                    if s_head not in focus_shape_state['inferred']:
                        focus_shape_state['inferred'].add(s_head)
                    if s_head in remaining_targets:
                        for a in body:
                            focus_shape_state['inferred'].discard(a)  # de-allocating memory

                        self.register_target(s_head, "valid", shape_name, shapes_state)
                        state.remaining_targets.discard(s_head)
                        focus_shape_state['remaining_targets_count'] -= 1

            self.stats.updateValidationLog("\nGrounded rules. \n")
            end = time.time()*1000.0
            self.stats.recordInterleavingTime(end - start)
            state.evaluated_predicates.add(query_rp_head[0])
        return skip_q

    @staticmethod
    def get_max_refs(shape, evaluated_predicates):
        """
        Checks if min&max query with the same inter-shape constraint exists and return all the shape names for those
        references that were already validated

        :param shape:
        :param evaluated_predicates:
        :return:
        """
        max_refs = {}
        skip_q = set()
        for max_c in shape.getConstraints():
            if max_c.max != -1 and max_c.shapeRef is not None and max_c.shapeRef in evaluated_predicates:
                for min_c in shape.getConstraints():
                    if min_c.min != -1 and min_c.shapeRef == max_c.shapeRef:
                        max_refs[max_c.shapeRef] = max_c.max
                        for constrRef, query_id in shape.maxConstrId.items():
                            if constrRef.shapeRef == max_c.shapeRef:
                                skip_q.add(query_id)
        return max_refs, skip_q

    def retrieve_next_targets(self, state, next_focus_shape, shapes_state):
        """
        Runs query to get targets of the next focus shape. If the query is run using filtering, pending_targets are
        added to set of remaining targets and invalid_targets are directly classified.
        The query can filter its answers using (in)validated targets given by an evaluated referenced shape (if any).
        """
        self.stats.updateValidationLog("\n\n>>>>>\nRetrieving (next) targets ...")
        if next_focus_shape.getTargetQuery() is None:
            return set()

        next_focus_shape_name = next_focus_shape.getId()
        state.prev_eval_shape_name = self.get_eval_child_name(next_focus_shape, state.visited_shapes)

        if self.selectivity_enabled and state.prev_eval_shape_name is not None:
            pending_targets, invalid_targets = self.InstRetrieval.extract_targets_with_filter(
                                                    next_focus_shape, self.eval_type, state.prev_eval_shape_name)
            for t in invalid_targets:
                self.register_target(t, "violated", next_focus_shape_name, shapes_state)
                shapes_state[next_focus_shape_name]['inferred'].add((t[0], t[1], not t[2]))
                shapes_state[next_focus_shape_name]['remaining_targets_count'] -= 1
        else:
            pending_targets = self.InstRetrieval.extract_targets(next_focus_shape)

        shapes_state[next_focus_shape_name]['remaining_targets_count'] = len(pending_targets)
        return pending_targets

    @staticmethod
    def get_eval_child_name(focus_shape, visited_shapes):
        """
        Returns the name of a shape that was already evaluated if it is referenced by the focus shape and contains
        relevant information for query filtering:
            - the number of valid or invalid targets is less than a threshold (currently set as 256),
            - the list of invalid targets is not empty,
            - the referenced shape has a target query defined.

        :param focus_shape: current shape being evaluated
        :param visited_shapes: set with names of shapes that were already evaluated
        :return: string with the (best) previously evaluated shape name or None if no shape fulfills the conditions
        """
        best_ref = None
        best_val_threshold = 256
        best_inv_threshold = 256
        for prev_shape in visited_shapes:
            prev_shape_name = prev_shape.getId()
            if focus_shape.referencedShapes.get(prev_shape_name) is not None:
                len_val = len(prev_shape.getValidTargets())
                len_inv = len(prev_shape.getInvalidTargets())

                if (0 < len_val < best_val_threshold) or (0 < len_inv < best_inv_threshold):
                    if len_inv > 0 and prev_shape.getTargetQuery() is not None:
                        best_ref = prev_shape_name
        return best_ref

    def register_target(self, t, t_type, invalidating_shape_name, shapes_state):
        """
        Adds each target to the set of valid/invalid instances of a shape.

        :param t: target
        :param t_type: string value that tells whether 't' is a valid target ('valid') or a 'violated' one
        :param invalidating_shape_name: name of the shape that (in)validates target 't'
        :param shapes_state: current validation's state of each shape
        """
        instance = "<" + t[1] + ">"
        self.shapes_dict[t[0]].targets[t_type].add(instance)
        shapes_state[invalidating_shape_name]['registered_targets'][t_type].add(t)
        self.traces.add(''.join([t_type, ", ",
                                 str(len(self.traces)), ", ",
                                 str(round(time.time() * 1000.0 - self.start_of_verification)), "\n"]))

    @staticmethod
    def write_targets_to_file(output_dir_name, all_valid_targets, all_invalid_targets, eval_type):
        if eval_type == "valid" or eval_type == "all":
            valid_targets_file = fileManagement.openFile(output_dir_name, "targets_valid.log")
            for t in all_valid_targets:
                lit_sign_str = "" if t[2] else "!"
                lit_str = lit_sign_str + t[0] + "(" + t[1] + ")"  # get string representation of tuple
                valid_log = lit_str + ",\n"
                valid_targets_file.write(valid_log)
            fileManagement.closeFile(valid_targets_file)

        if eval_type == "violated" or eval_type == "all":
            violated_targets_file = fileManagement.openFile(output_dir_name, "targets_violated.log")
            for t in all_invalid_targets:
                lit_sign_str = "" if t[2] else "!"
                lit_str = lit_sign_str + t[0] + "(" + t[1] + ")"
                invalid_log = lit_str + ",\n"
                violated_targets_file.write(invalid_log)
            fileManagement.closeFile(violated_targets_file)

    def validation_output(self, shapes_state):
        """
        Saves to local file the (in)validated targets and returns result of validation

        :return: dictionary containing shape names and their respective (in)validated targets
        """
        output = {}
        all_valid_targets = set()
        all_invalid_targets = set()
        for shape_name in self.shapes_dict.keys():
            validated_targets = shapes_state[shape_name]['registered_targets']['valid']
            invalidated_targets = shapes_state[shape_name]['registered_targets']['violated']

            output[shape_name] = {
                "valid_instances": validated_targets,
                "invalid_instances": invalidated_targets,
            }
            all_valid_targets.update(validated_targets)
            all_invalid_targets.update(invalidated_targets)
        all_valid_targets.update(self.valid_targets_after_termination)

        if self.save_targets_to_file:
            self.write_targets_to_file(self.output_dir_name, all_valid_targets, all_invalid_targets, self.eval_type)

        if self.save_stats:
            validation_log = fileManagement.openFile(self.output_dir_name, "validation.log")
            stats = fileManagement.openFile(self.output_dir_name, "stats.txt")
            traces = fileManagement.openFile(self.output_dir_name, "traces.csv")

            self.stats.recordTargets(len(all_valid_targets) + len(all_invalid_targets))
            self.stats.writeAll(stats)
            fileManagement.closeFile(stats)

            self.stats.writeValidationLog(validation_log)
            validation_log.write("\nValid targets: " + str(len(all_valid_targets)))
            validation_log.write("\nInvalid targets: " + str(len(all_invalid_targets)))
            fileManagement.closeFile(validation_log)

            traces.write("Target, #TripleInThatNode, TimeSinceStartOfVerification(ms)\n")
            for trace in self.traces:
                traces.write(trace)
            fileManagement.closeFile(traces)

        # add to output all targets that could not be (in)validated by any shape
        output["unbound"] = {"valid_instances": self.valid_targets_after_termination}
        return output


class ValidationState:
    def __init__(self, shapes_dict):
        self.remaining_targets = set()
        self.visited_shapes = set()
        self.evaluated_predicates = set()
        self.prev_eval_shape_name = None
        self.shapes_state = {}
        self.preds_to_shapes = {}

        for shape_name in shapes_dict.keys():
            self.shapes_state[shape_name] = {
                "inferred": set(),
                "pending_refs_to_saturate": len(shapes_dict[shape_name].referencedShapes.keys()),
                "remaining_targets_count": 0,
                "rule_map": {},
                "registered_targets": {"valid": set(), "violated": set()}
            }
            for pred in shapes_dict[shape_name].predicates:
                self.preds_to_shapes[pred] = shape_name
