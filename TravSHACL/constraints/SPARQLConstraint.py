# -*- coding: utf-8 -*-
__author__ = 'Philipp D. Rohde'

from TravSHACL.constraints.Constraint import Constraint


class SPARQLConstraint(Constraint):
    """This class represents max constraints, i.e., a constraint for the maximal occurrence of a path."""

    def __init__(self, id_, is_pos, query: str = None):
        """
        Creates a new SPARQL constraint.

        :param id_: name of the constraint
        :param query: a string representing the SPARQL query to be executed for the constraint evaluation
        """
        super().__init__(id_, is_pos, None, None, None, None, None, None, None)
        self.min = -1
        self.max = -1
        self.query = query
