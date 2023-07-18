# -*- coding: utf-8 -*-
__author__ = 'Monica Figuera and Philipp D. Rohde'


class Constraint:
    """Base class for all constraints."""

    def __init__(self, id_=None, is_pos=None, satisfied=None, datatype=None, value=None,
                 shape_ref=None, target_def=None, path=None, options=None):
        """
        Base constructor for all constraints.

        :param id_: name of the constraint
        :param is_pos: true if it is a positive constraint, false otherwise
        :param satisfied: indicates whether the constraint is satisfied, should be unknown at creation
        :param datatype: contains the datatype the object must fulfill
        :param value: contains the value the constraint checks again, i.e., an object
        :param shape_ref: contains the name of the shape referenced by the constraint, none otherwise
        :param target_def: contains the target definition of the shape the constraint belongs to if it has one
        :param path: the path associated with this constraint, e.g., a predicate
        :param options: gets the options to be used in or_operation
        """
        self.id = id_
        self.isPos = is_pos
        self.satisfied = satisfied
        self.options = options
        self.datatype = datatype
        self.value = value
        self.shapeRef = shape_ref
        self.target = target_def

        self.variables = []
        self.path = path

    def get_datatype(self):
        return self.datatype

    def get_value(self):
        return self.value

    def get_shape_ref(self):
        return self.shapeRef

    def get_id(self):
        return self.id

    def get_is_pos(self):
        return self.isPos

    def get_options(self):
        return self.options

    @staticmethod
    def generate_variables(var_generator, type_, number_of_variables):
        """Generates variable names for the SPARQL queries of the constraint."""
        vars_ = []
        if number_of_variables:
            for elem in range(number_of_variables):
                vars_.append(var_generator.generate_variable(type_))

        return vars_

    def get_variables(self):
        return self.variables

    def compute_rule_pattern_body(self):
        """
        Compute the body of the rule patterns representing the constraint.

        :return: rule pattern body of the constraint
        """
        return [(self.shapeRef, v, self.isPos) for v in self.variables] if self.shapeRef is not None else []
