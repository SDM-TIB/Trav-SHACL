# -*- coding: utf-8 -*-
import itertools
from enum import Enum

i = itertools.count()


class VariableGenerator:
    def __init__(self):
        self.index = 0

    #def incrementAndGet(self):
    #    self.index += 1
    #    return self.index

    @staticmethod
    def generateVariable(type):
        type = "p_"  # *** hardcoded
        return str(type) + str(next(i))

    @staticmethod
    def getFocusNodeVar():
        return "x"  # ***


class VariableType(Enum):
    VALIDATION = "p_"
    VIOLATION = "n_"  # not used

    @classmethod
    def prefix(cls):
        return cls.VALIDATION
