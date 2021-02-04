# -*- coding: utf-8 -*-

class Query:
    def __init__(self, id, rulePattern, sparql):
        self.id = id
        self.rulePattern = rulePattern
        self.sparql = sparql

    def getId(self):
        return self.id

    def getRulePattern(self):
        return self.rulePattern

    def getSparql(self):
        return self.sparql
