# -*- coding: utf-8 -*-
__author__ = 'Monica Figuera'


class RulePattern:
    """Implementation of Datalog-like rules."""

    def __init__(self, head, body):
        self.__head = head
        self.__literals = body
        self.__variables = set([head[1]] + [a[1] for a in body if a is not None])

    def __repr__(self):
        return '[' + str(self.head) + '] <-- ' + str(self.body)

    @property
    def head(self):
        return self.__head

    @property
    def body(self):
        return self.__literals

    @property
    def variables(self):
        return self.__variables
