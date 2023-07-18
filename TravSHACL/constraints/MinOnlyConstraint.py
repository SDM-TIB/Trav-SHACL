# -*- coding: utf-8 -*-
__author__ = 'Monica Figuera and Philipp D. Rohde'

from TravSHACL.utils.VariableGenerator import VariableType
from TravSHACL.constraints.Constraint import Constraint


class MinOnlyConstraint(Constraint):
    """This class represents min constraints, i.e., a constraint for the minimal occurrence of a path."""

    def __init__(self, var_generator, id_, path, min_, is_pos, options, datatype=None, value=None, shape_ref=None, target_def=None):
        """
        Creates a new min constraint.

        :param var_generator: variable generator instance
        :param id_: name of the constraint
        :param path: the path associated with this constraint, e.g., a predicate
        :param min_: the minimal occurrence allowed
        :param is_pos: true if it is a positive constraint, false otherwise
        :param datatype: contains the datatype the object must fulfill
        :param value: contains the value the constraint checks again, i.e., an object
        :param shape_ref: contains the name of the shape referenced by the constraint, none otherwise
        :param target_def: contains the target definition of the shape the constraint belongs to if it has one
        """
        super().__init__(id_, is_pos, None, datatype, value, shape_ref, target_def, path, options)
        self.varGenerator = var_generator
        self.min = min_
        self.max = -1
        self.variables = self.compute_variables()

    def compute_variables(self):
        """Computes variable names for the SPARQL queries of the constraint."""
        atomic_constraint = Constraint()
        return atomic_constraint.generate_variables(self.varGenerator, VariableType.VALIDATION, self.min)
