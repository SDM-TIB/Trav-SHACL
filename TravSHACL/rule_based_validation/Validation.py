# -*- coding: utf-8 -*-
__author__ = 'Monica Figuera'

import time

from TravSHACL.rule_based_validation.InstancesRetrieval import InstancesRetrieval
from TravSHACL.sparql.SPARQLEndpoint import SPARQLEndpoint
from TravSHACL.utils import fileManagement
from TravSHACL.utils.ValidationStats import ValidationStats


class Validation:
    """This class is responsible for managing the validation process."""

    def __init__(self, endpoint: SPARQLEndpoint, node_order, shapes_dict, target_shape_predicates,
                 use_selective_queries, output_dir_name, save_stats, save_targets_to_file):
        """
        Creates a new instance for the validation process.

        :param endpoint: SPARQL endpoint which is validated
        :param node_order: indicates the order in which the shapes will be evaluated
        :param shapes_dict: a Python dictionary holding all shapes of the shape schema
        :param target_shape_predicates: names of the shapes with a target definition
        :param use_selective_queries: indicates whether selective queries will be used
        :param output_dir_name: path for the output files
        :param save_stats: indicates whether statistics will be saved to the output path
        :param save_targets_to_file: indicates whether target classifications will be saved to the output path
        """
        self.node_order = node_order
        self.shapes_dict = shapes_dict
        self.target_shape_predicates = target_shape_predicates
        self.selectivity_enabled = use_selective_queries

        self.output_dir_name = output_dir_name
        self.save_stats = save_stats
        self.save_targets_to_file = save_targets_to_file
        self.stats = ValidationStats()
        self.traces = set()

        self.stats.update_log('Node order: ' + str(self.node_order) + '\n')
        self.InstRetrieval = InstancesRetrieval(endpoint, shapes_dict, self.stats)
        self.valid_targets_after_termination = set()
        self.start_of_verification = time.time()

    def exec(self):
        """Executes the validation process of the entire shape schema."""
        focus_shape = self.shapes_dict[self.node_order.pop(0)]
        state = ValidationState(self.shapes_dict)
        initial_targets = self.retrieve_next_targets(state, focus_shape, state.shapes_state)
        state.remaining_targets.update(initial_targets)
        state.shapes_state[focus_shape.get_id()]['remaining_targets_count'] = len(initial_targets)

        start = time.time() * 1000.0
        self.validate(state, focus_shape)
        finish = time.time() * 1000.0
        elapsed = round(finish - start)
        self.stats.record_total_time(elapsed)
        self.stats.record_total_rules(state.total_rule_number)
        self.stats.update_log('\n\nMaximal number or rules in memory: ' + str(self.stats.max_rules))
        self.stats.update_log('\nTotal number of rules: ' + str(state.total_rule_number))
        return self.validation_output(state.shapes_state)

    def validate(self, state, focus_shape):
        """
        Validates a shape.

        :param state: current validation state
        :param focus_shape: focus shape to be evaluated
        """
        if len(state.visited_shapes) == len(self.shapes_dict) or focus_shape is None:
            self.valid_targets_after_termination.update(state.remaining_targets)
            return

        self.stats.update_log('\n\n>>>>> Starting validation of shape: ' + focus_shape.get_id())
        state.evaluated_predicates.add(focus_shape.get_id())
        self.eval_shape(state, focus_shape, state.shapes_state)

        next_focus_shape = None
        if len(self.node_order) > 0:
            next_focus_shape = self.shapes_dict[self.node_order.pop(0)]
            pending_targets = self.retrieve_next_targets(state, next_focus_shape, state.shapes_state)
            state.remaining_targets.update(pending_targets)

        self.validate(state, next_focus_shape)

    def retrieve_next_targets(self, state, next_focus_shape, shapes_state):
        """
        Runs query to get targets of the next focus shape. If the query was rewritten (filtering), pending_targets are
        added to set of remaining targets and invalid_targets are directly classified.

        :param state: current overall validation state
        :param next_focus_shape: the upcoming focus shape, i.e., the shape all possible targets need to be collected for
        :param shapes_state: dictionary storing validation's state of each shape
        :return: all pending targets for the upcoming focus shape
        """
        self.stats.update_log('\n\n>>>>>\nRetrieving (next) targets ...')
        if next_focus_shape.get_target_query() is None:
            return set()

        next_focus_shape_name = next_focus_shape.get_id()
        filtering_shape = self.get_evaluated_out_neighbor(next_focus_shape, state.visited_shapes, state)
        shapes_state[next_focus_shape_name]['filtering_shape'] = filtering_shape
        max_ref = next_focus_shape.is_max_ref(filtering_shape.get_id()) if filtering_shape is not None else True  # TODO: check if filtering based on max constraints is possible
        if self.selectivity_enabled and filtering_shape is not None and not max_ref:
            # A query can filter its answers with (in)validated targets given by an evaluated out-neighboring shape
            pending, invalid = self.InstRetrieval.extract_targets_with_filter(next_focus_shape, filtering_shape)
            for target in invalid:
                self.register_target(target, 'violated', next_focus_shape_name, shapes_state)
                shapes_state[next_focus_shape_name]['inferred'].add((target[0], target[1], not target[2]))
                shapes_state[next_focus_shape_name]['remaining_targets_count'] -= 1
        else:
            pending = self.InstRetrieval.extract_targets(next_focus_shape)

        # checking for 'or' constraint
        if next_focus_shape.flag:
            invalid_pending = []
            pending_val = self.InstRetrieval.extract_options(next_focus_shape)
            for target in pending:
                if pending_val:
                    if target not in pending_val:
                        invalid_pending.append(target)
                        self.register_target(target, "violated", next_focus_shape_name, shapes_state)
                        shapes_state[next_focus_shape_name]['inferred'].add((target[0], target[1], not target[2]))
                        shapes_state[next_focus_shape_name]['remaining_targets_count'] -= 1

            pending = [target for target in pending if target not in invalid_pending]

        # check the SPARQL constraints
        sparql_constraints = next_focus_shape.get_sparql_constraints()
        if len(sparql_constraints) > 0:
            for constraint in sparql_constraints:
                violations = self.InstRetrieval.execute_sparql_constraint(
                    constraint_id=constraint.id,
                    query_str=constraint.query,
                    instance_list=[p[1] for p in pending]
                )
                pending = {target for target in pending if target[1] not in violations}
                for invalid in violations:
                    target = (next_focus_shape_name, invalid, False)
                    self.register_target(target, 'violated', next_focus_shape_name, shapes_state)
                    shapes_state[next_focus_shape_name]['inferred'].add((target[0], target[1], not target[2]))
                    shapes_state[next_focus_shape_name]['remaining_targets_count'] -= 1

        shapes_state[next_focus_shape_name]['remaining_targets_count'] = len(pending)
        return pending

    @staticmethod
    def get_evaluated_out_neighbor(focus_shape, visited_shapes, state):
        """
        Returns the name of an outgoing neighboring shape (i.e., object in inter-shape constraint of 'focus_shape')
        that was already evaluated and contains relevant information for query filtering:
            - the number of valid or invalid targets is less than a threshold (currently set as 256),
            - the list of invalid targets is not empty,
            - the neighboring shape has a target query defined.

        :param focus_shape: current shape being evaluated
        :param visited_shapes: set with names of shapes that were already evaluated
        :param state: object keeping track of the current validation state
        :return: reference to the (best) previously evaluated shape, or None if no shape fulfills the conditions
        """
        best_filtering_shape = None
        best_val_threshold = 256
        best_inv_threshold = 256
        for prev_shape in visited_shapes:
            prev_shape_name = prev_shape.get_id()
            if focus_shape.referencedShapes.get(prev_shape_name) is not None:
                len_val = len(prev_shape.get_valid_targets())
                len_inv = len(prev_shape.get_invalid_targets())

                if (0 < len_val < best_val_threshold) or (0 < len_inv < best_inv_threshold):
                    if len_inv > 0 and prev_shape.get_target_query() is not None:
                        if state.shapes_state[prev_shape_name]['remaining_targets_count'] == 0:
                            best_filtering_shape = prev_shape

        return best_filtering_shape

    def eval_shape(self, state, shape, shapes_state):
        """
        Interleaves 'shape' entities and performs a deferred saturation for entities that could not be validated during
        the interleaving because of missing information to be provided by (not yet evaluated) out-neighboring shapes.

        :param state: object keeping track of the current validation state
        :param shape: focus shape to be evaluated
        :param shapes_state: dictionary storing validation's state of each shape
        """
        shape_name = shape.get_id()

        self.eval_constraints_queries(state, shape, shapes_state[shape_name]['filtering_shape'])  # interleave

        self.stats.update_log('\nStarting saturation ...')
        start = time.time() * 1000.0
        self.saturate_remaining(state, shape_name, shapes_state)
        end = time.time() * 1000.0

        self.stats.record_saturation_time(end - start)
        self.stats.update_log('\nsaturation ...\nelapsed: ' + str(end - start) + ' ms')

        state.visited_shapes.add(shape)
        self.stats.update_log('\nRemaining targets: ' + str(len(state.remaining_targets)))

    def eval_constraints_queries(self, state, shape, filtering_shape):
        """
        Evaluates all constraints queries of focus 'shape'.
        There is one query with all min constraints and (possibly) one query per max constraint.

        :param state: object keeping track of the current validation state
        :param shape: focus shape to be evaluated
        :param filtering_shape: shape (referenced by focus 'shape') providing filtering instances
        """
        shape_rp = shape.get_rule_pattern()
        shape_name = shape.get_id()
        shapes_state = state.shapes_state
        remaining_targets = state.remaining_targets

        if shape.minQuery is None and not shape.maxQueries:  # current shape is a shape without constraints
            to_remove = []
            for head in remaining_targets:
                if head[0] == shape_name:
                    self.register_target(head, 'valid', shape_name, shapes_state)
                    to_remove.append(head)
                    shapes_state[shape_name]['remaining_targets_count'] -= 1
                    shapes_state[shape_name]['inferred'].add(head)
            for head in to_remove:
                remaining_targets.discard(head)

        if shape.minQuery is not None:
            min_query_rp = shape.minQuery.get_rule_pattern()
            self.interleave(state, shape, shape.minQuery, filtering_shape, min_query_rp, shape_rp, 'min')

        for q in shape.maxQueries:
            max_query_rp = q.get_rule_pattern()
            self.interleave(state, shape, q, filtering_shape, max_query_rp, shape_rp, 'max')
            # after running the max constraints, rules need to be added for the instances that were not
            # in the query result since they will still be valid and may need to be checked further
            for head in remaining_targets:
                if head[0] == shape_name:
                    body = set()
                    for i, atom_pattern in enumerate(shape_rp.body):
                        a = (atom_pattern[0], head[1], atom_pattern[2])
                        body.add(a)

                    s_head = (shape_name, head[1], True)

                    if s_head not in state.rule_map.keys():
                        s = set()
                        s.add(frozenset(body))
                        state.rule_map[s_head] = s
                        state.rule_number += 1
                        state.total_rule_number += 1
                    else:
                        if frozenset(body) not in state.rule_map[s_head]:
                            state.rule_number += 1
                            state.total_rule_number += 1
                        state.rule_map[s_head].add(frozenset(body))

    def interleave(self, state, shape, q, filtering_shape, q_rule_pattern, s_rule_pattern, q_type):
        """
        Evaluates corresponding min/max query of 'shape' and starts interleaving process for all answers retrieved.

        Query 'q' can be rewritten to include a filter (VALUES clause) with the targets of 'filtering_shape', and
        (possibly) partitioned when the number of filtering instances exceeds a given threshold.

        Each grounded rule is composed of literals (an atom or its negation).
        Each atom 'a' is a tuple with 3 fields: a[0] - predicate, a[1] - instance (entity), a[2] - sign (True or False)

        :param state: current state of the validation
        :param shape: focus shape
        :param q: constraint query to be evaluated
        :param filtering_shape: shape (referenced by focus 'shape') providing filtering instances
        :param q_rule_pattern: query rule pattern
        :param s_rule_pattern: shape rule pattern
        :param q_type: query type ('min' or 'max')
        """
        shapes_state = state.shapes_state
        preds_to_shapes = state.preds_to_shapes
        shape_name = shape.get_id()
        t_state = shapes_state[shape_name]  # focus shape's state

        query_rp_head = q_rule_pattern.head
        query_rp_body = q_rule_pattern.body
        shape_rp_head = s_rule_pattern.head
        shape_rp_body = s_rule_pattern.body

        q_body_ref_shapes = [preds_to_shapes[pattern[0]] for pattern in query_rp_body]
        s_body_ref_shapes = [preds_to_shapes[pattern[0]] for pattern in shape_rp_body]
        shape_max_refs = shape.get_max_query_valid_refs()
        inter_constr_count = {}
        new_rules_count = 0
        rules_directly_inferred = 0

        for query_str in self.InstRetrieval.rewrite_constraint_query(shape, q, filtering_shape, q_type, self.selectivity_enabled):
            start = time.time() * 1000.0
            for b in self.InstRetrieval.run_constraint_query(q, query_str):
                q_head = (query_rp_head[0], b[query_rp_head[1]]['value'], query_rp_head[2])
                s_head = (shape_rp_head[0], b[shape_rp_head[1]]['value'], shape_rp_head[2])

                body = set()
                is_body_inferred = True
                is_body_inferrable = True
                negated_body = False
                for i, atom_pattern in enumerate(query_rp_body):
                    a_state = shapes_state[q_body_ref_shapes[i]]  # body atom's shape state
                    a = (atom_pattern[0], b[atom_pattern[1]]['value'], atom_pattern[2])
                    body.add(a)
                    if a[0] in state.evaluated_predicates:  # exclude not yet evaluated atom's query
                        if state.rule_map.get((a[0], a[1], True)) is None:
                            if a not in a_state['inferred']:
                                if (a[0], a[1], not a[2]) not in a_state['inferred']:
                                    is_body_inferred = False
                                    continue  # exclude non-selective answers from interleaving
                                else:
                                    is_body_inferred = False
                                    is_body_inferrable = False
                        else:
                            is_body_inferred = False

                        # if interleaving min-query with an upper bound <> None -> verify upper bound violations
                        if a in a_state['inferred'] \
                                and q_type == 'min' \
                                and shape_max_refs.get(q_body_ref_shapes[i]) is not None:
                            if inter_constr_count.get(s_head) is None:
                                inter_constr_count[s_head] = {inter_constraint: set() for inter_constraint in shape_max_refs}
                            inter_constr_count[s_head][q_body_ref_shapes[i]].add(a)
                            if len(inter_constr_count[s_head][q_body_ref_shapes[i]]) > shape_max_refs[q_body_ref_shapes[i]]:
                                negated_body = True  # if number of instantiations exceeds max value -> infer negation
                    else:
                        is_body_inferred = False

                if negated_body:
                    # case (2) - infer negation of rule head (given negated body atom)
                    t_state['inferred'].add((q_head[0], q_head[1], False))
                    if s_head[2] and s_head in state.remaining_targets:
                        self.register_target(s_head, 'violated', shape_name, shapes_state)
                        state.remaining_targets.discard(s_head)
                        t_state['remaining_targets_count'] -= 1
                    continue

                # case (3) - add pending rule / infer query head
                if not is_body_inferred:
                    if is_body_inferrable:
                        if q_head not in state.rule_map.keys():
                            s = set()
                            s.add(frozenset(body))
                            state.rule_map[q_head] = s
                            new_rules_count += 1
                        else:
                            if frozenset(body) not in state.rule_map[q_head]:
                                new_rules_count += 1
                                state.rule_map[q_head].add(frozenset(body))
                else:
                    t_state['inferred'].add(q_head)
                    rules_directly_inferred += 1

                # Shape rule pattern #
                body = set()
                is_body_inferred = True
                negated_body = False
                for i, atom_pattern in enumerate(shape_rp_body):
                    a_state = shapes_state[s_body_ref_shapes[i]]
                    a = (atom_pattern[0], b[atom_pattern[1]]['value'], atom_pattern[2])
                    body.add(a)
                    if a not in a_state['inferred']:
                        if (a[0], a[1], not a[2]) not in a_state['inferred']:
                            is_body_inferred = False
                            continue  # non-selective (when retrieved objects of a triple that do not match any target)

                        # case (1) - if negated (unmatchable) body atoms
                        elif (a[0], a[1], not a[2]) in a_state['inferred']:
                            negated_body = True
                            break
                        else:
                            is_body_inferred = False

                if negated_body:
                    # case (2) - infer negation of rule head (negated body atom)
                    t_state['inferred'].add((s_head[0], s_head[1], False))
                    if s_head[2] and s_head in state.remaining_targets:
                        self.register_target(s_head, 'violated', shape_name, shapes_state)
                        state.remaining_targets.discard(s_head)
                        t_state['remaining_targets_count'] -= 1
                    continue

                # case (3) - add pending rule / classify valid target (all body inferred)
                if not is_body_inferred:
                    if s_head not in state.rule_map.keys():
                        s = set()
                        s.add(frozenset(body))
                        state.rule_map[s_head] = s
                        new_rules_count += 1
                    else:
                        if frozenset(body) not in state.rule_map[s_head]:
                            new_rules_count += 1
                            state.rule_map[s_head].add(frozenset(body))
                else:
                    if s_head not in t_state['inferred']:
                        t_state['inferred'].add(s_head)
                    if s_head in state.remaining_targets:
                        for a in body:
                            t_state['inferred'].discard(a)  # de-allocating memory

                        self.register_target(s_head, 'valid', shape_name, shapes_state)
                        state.remaining_targets.discard(s_head)
                        t_state['remaining_targets_count'] -= 1
                    rules_directly_inferred += 1

            self.stats.update_log('\nGrounded rules. \n')
            end = time.time()*1000.0
            self.stats.record_interleaving_time(end - start)
            state.evaluated_predicates.add(query_rp_head[0])

        all_current_rules = new_rules_count + rules_directly_inferred
        state.rule_number += new_rules_count
        state.total_rule_number += all_current_rules
        self.stats.update_log('\n\nNumber of rules: ' + str(all_current_rules))
        self.stats.record_current_number_of_rules(all_current_rules)

    def saturate_remaining(self, state, shape_name, shapes_state):
        """
        The saturation process consists of two steps:
        1. Negate: same as in step (1) of interleaving process
        2. Infer: same is step (2) of interleaving process
        Repeat 1 and 2 until no further changes are made (i.e., no new inferences found)

        :param state: current state of the validation
        :param shape_name: name of focus shape or its 'parents' (after recursion)
        :param shapes_state: dictionary storing validation's state of each shape
        """
        rule_map = state.rule_map
        negated = self.negate_unmatchable_heads(state, rule_map, state.evaluated_predicates, shape_name, shapes_state, state.preds_to_shapes)
        inferred = self.apply_rules(state, state.remaining_targets, rule_map, shape_name, shapes_state, state.preds_to_shapes)
        if negated or inferred:
            self.saturate_remaining(state, shape_name, shapes_state)

    def negate_unmatchable_heads(self, state, rule_map, evaluated_predicates, shape_name, shapes_state, preds_to_shapes):
        """
        Derives negation of atoms that are not satisfied. An atom 'a' is not satisfied when:
        its query (predicate) was already evaluated, positive 'a' is not a rule head, and 'a' is not inferred yet.

        :param state: current state of the validation
        :param rule_map: set of pending rules associated to either focus shape or an incoming neighbor after recursion
        :param evaluated_predicates: target/min/max query predicates evaluated so far
        :param shape_name: string name of the focus shape
        :param shapes_state: dictionary storing validation's state of each shape
        :param preds_to_shapes: dictionary that maps predicate names to shape names
        :return: True if new negative inferences were found, False otherwise
        """
        new_negated_atom_found = False
        all_body_atoms = set(frozenset().union(*set().union(*rule_map.values())))
        for a in all_body_atoms:
            a_state = shapes_state[preds_to_shapes[a[0]]]  # atom's shape state (gets shape id from the constraint id)
            if a[0] in evaluated_predicates \
                    and rule_map.get((a[0], a[1], True)) is None \
                    and a not in a_state['inferred']:  # if atom 'a' is not satisfied
                negated_atom = (a[0], a[1], False)
                if negated_atom not in a_state['inferred']:
                    new_negated_atom_found = True
                    a_state['inferred'].add(negated_atom)

        remaining = set()
        for a in state.remaining_targets:
            t_state = shapes_state[a[0]]  # target's shape state
            if a[0] in evaluated_predicates \
                    and rule_map.get((a[0], a[1], True)) is None \
                    and a not in t_state['inferred']:  # if atom 'a' is not satisfied
                self.register_target(a, 'violated', shape_name, shapes_state)
                t_state['inferred'].add((a[0], a[1], not a[2]))
                t_state['remaining_targets_count'] -= 1
            else:
                remaining.add(a)
        state.remaining_targets = remaining
        return new_negated_atom_found

    def apply_rules(self, state, remaining_targets, rule_map, shape_name, shapes_state, preds_to_shapes):
        """
        Performs two types of inferences:
        # case (1): If the rule map contains a rule and some rule bodies were inferred
                    => head of the rule is inferred, rule dropped.
        # case (2): If the negation of any rule body was inferred
                    => the rule cannot be applied (rule head not inferred), rule dropped.

        :param state: current state of the validation
        :param remaining_targets: pending targets, i.e., targets that are neither valid nor invalid yet
        :param rule_map: set of pending rules associated to either focus shape or an incoming neighbor after recursion
        :param shape_name: name of the current focus shape
        :param shapes_state: dictionary storing validation's state of each shape
        :param preds_to_shapes: dictionary that maps predicate names to shape names
        :return: True if new inferences were found, False otherwise
        """
        fresh_literals = False
        rule_map_copy = rule_map.copy()
        for head, bodies in rule_map_copy.items():
            head_shape_name = preds_to_shapes[head[0]]
            inferred_bodies = set()
            for body in bodies:
                inferred_atoms = {'F_atom' if (a[0], a[1], not a[2]) in shapes_state[preds_to_shapes[a[0]]]['inferred']
                                  else ('T_atom' if a in shapes_state[preds_to_shapes[a[0]]]['inferred']
                                        else 'P_atom') for a in body}
                if 'T_atom' in inferred_atoms and len(inferred_atoms) == 1:
                    inferred_bodies.add('T')
                elif 'F_atom' in inferred_atoms:
                    inferred_bodies.add('F')
                else:
                    inferred_bodies.add('P')

            if 'T' in inferred_bodies:  # case (1)
                fresh_literals = True
                if head in remaining_targets:
                    self.register_target(head, 'valid', shape_name, shapes_state)
                    remaining_targets.discard(head)
                    shapes_state[head_shape_name]['remaining_targets_count'] -= 1
                shapes_state[head_shape_name]['inferred'].add(head)
                del rule_map[head]
                state.rule_number -= len(bodies)
            elif 'F' in inferred_bodies and 'P' not in inferred_bodies:  # case (2)
                fresh_literals = True
                if head in remaining_targets:
                    self.register_target(head, 'violated', shape_name, shapes_state)
                    remaining_targets.discard(head)
                    shapes_state[head_shape_name]['remaining_targets_count'] -= 1
                shapes_state[head_shape_name]['inferred'].add((head[0], head[1], not head[2]))
                del rule_map[head]
                state.rule_number -= len(bodies)

        if not fresh_literals:
            return False
        self.stats.update_log('\nRemaining targets: ' + str(len(remaining_targets)))
        return True

    def register_target(self, t, t_type, invalidating_shape_name, shapes_state):
        """
        Adds each target to the set of valid/invalid instances of a shape.

        :param t: target tuple: t[0] - predicate (string), t[1] - instance (string), t[2] - sign (boolean)
        :param t_type: string value that tells whether 't' is a valid target ('valid') or a 'violated' one
        :param invalidating_shape_name: string name of the shape that (in)validates target 't'
        :param shapes_state: dictionary storing validation's state of each shape
        """
        instance = '<' + t[1] + '>'
        self.shapes_dict[t[0]].targets[t_type].add(instance)
        shapes_state[invalidating_shape_name]['registered_targets'][t_type].add(t)
        self.traces.add(''.join([invalidating_shape_name, ',', t_type, ',',
                        str(len(self.traces) + 1), ',',
                        str(time.time() - self.start_of_verification), '\n']))

    @staticmethod
    def write_targets_to_file(output_dir_name, all_valid_targets, all_invalid_targets):
        """Writes all target classifications to file, i.e., one file for valid targets and one for invalid ones."""
        def write_list_to_file(list_, file_):
            """Helper function to write a list to file."""
            for elem in list_:
                lit_sign_str = '' if elem[2] else '!'
                lit_str = lit_sign_str + elem[0] + '(' + elem[1] + ')'  # get string representation of tuple
                file_.write(lit_str + ',\n')

        valid_targets_file = fileManagement.open_file(output_dir_name, 'targets_valid.log')
        write_list_to_file(all_valid_targets, valid_targets_file)
        fileManagement.close_file(valid_targets_file)

        violated_targets_file = fileManagement.open_file(output_dir_name, 'targets_violated.log')
        write_list_to_file(all_invalid_targets, violated_targets_file)
        fileManagement.close_file(violated_targets_file)

    def validation_output(self, shapes_state):
        """
        Saves to local file the (in)validated targets and returns result of validation

        :param shapes_state: dictionary storing validation's state of each shape
        :return: dictionary containing shape names and their respective (in)validated targets
        """
        output = {}
        all_valid_targets = set()
        all_invalid_targets = set()
        for shape_name in self.shapes_dict.keys():
            validated_targets = shapes_state[shape_name]['registered_targets']['valid']
            invalidated_targets = shapes_state[shape_name]['registered_targets']['violated']
            output[shape_name] = {
                'valid_instances': validated_targets,
                'invalid_instances': invalidated_targets,
            }
            all_valid_targets.update(validated_targets)
            all_invalid_targets.update(invalidated_targets)
        all_valid_targets.update(self.valid_targets_after_termination)

        if self.save_targets_to_file:
            self.write_targets_to_file(self.output_dir_name, all_valid_targets, all_invalid_targets)

        if self.save_stats:
            validation_log = fileManagement.open_file(self.output_dir_name, 'validation.log')
            stats = fileManagement.open_file(self.output_dir_name, 'stats.txt')
            traces = fileManagement.open_file(self.output_dir_name, 'traces.csv')

            self.stats.record_number_of_targets(len(all_valid_targets), len(all_invalid_targets))
            self.stats.write_all_stats(stats)
            fileManagement.close_file(stats)

            self.stats.write_validation_log(validation_log)
            validation_log.write('\nValid targets: ' + str(len(all_valid_targets)))
            validation_log.write('\nInvalid targets: ' + str(len(all_invalid_targets)))
            fileManagement.close_file(validation_log)

            traces.write('Shape,Result,Number,Time\n')
            for trace in self.traces:
                traces.write(trace)
            fileManagement.close_file(traces)

        # add to output all targets that could not be (in)validated by any shape
        output["unbound"] = {'valid_instances': self.valid_targets_after_termination}

        # TTL validation report
        if self.save_stats:
            if len(all_invalid_targets) == 0:
                output_ttl = ':report a sh:ValidationReport ;\n' + '  sh:conforms true '
            else:
                output_ttl = ':report a sh:ValidationReport ;\n' + '  sh:conforms false ;\n' + '  sh:result'
                for i, violation in enumerate(all_invalid_targets):
                    if i != 0:
                        output_ttl += ' ,'
                    output_ttl += '\n    [ a  sh:ValidationResult ;\n' +\
                                  '      sh:resultSeverity  sh:Violation ;\n' +\
                                  '      sh:focusNode  <' + violation[1] + '> ;\n' +\
                                  '      sh:sourceShape  ' + violation[0] + ' ]'

            output_ttl = '@prefix sh: <http://www.w3.org/ns/shacl#> . \n\n' + output_ttl + ' .'            
            validation_report = fileManagement.open_file(self.output_dir_name, 'validationReport.ttl')
            validation_report.write(output_ttl)
            fileManagement.close_file(validation_report)
        return output


class ValidationState:
    """This class is responsible for keeping track of the validation state."""

    def __init__(self, shapes_dict):
        self.remaining_targets = set()
        self.visited_shapes = set()
        self.evaluated_predicates = set()
        self.shapes_state = {}
        self.preds_to_shapes = {}  # maps all constraint ids to their respective shape ids
        self.rule_map = {}
        self.rule_number = 0
        self.total_rule_number = 0

        for shape_name in shapes_dict.keys():
            self.shapes_state[shape_name] = {
                'filtering_shape': None,
                'inferred': set(),
                'remaining_targets_count': 0,
                'registered_targets': {'valid': set(), 'violated': set()}
            }
            for pred in shapes_dict[shape_name].predicates:
                self.preds_to_shapes[pred] = shape_name
