# -*- coding: utf-8 -*-

import itertools
from enum import Enum

i = itertools.count()


class VariableGenerator:
    """Used to create unused variables for the SPARQL queries."""

    def __init__(self):
        self.index = 0

    @staticmethod
    def generate_variable(type_):
        type_ = 'p_'  # *** hardcoded
        return str(type_) + str(next(i))

    @staticmethod
    def get_focus_node_var():
        return 'x'  # *** hardcoded


class VariableType(Enum):
    VALIDATION = 'p_'
    VIOLATION = 'n_'  # not used

    @classmethod
    def prefix(cls):
        return cls.VALIDATION
