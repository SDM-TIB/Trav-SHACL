# -*- coding: utf-8 -*-


class RulePattern:
    def __init__(self, head, body):
        self.head = head
        self.literals = body
        self.variables = set([head[1]] + [a[1] for a in body if a is not None])

    def getHead(self):
        return self.head

    def getBody(self):
        return self.literals

    def getVariables(self):
        return self.variables
