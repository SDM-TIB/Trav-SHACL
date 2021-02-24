# -*- coding: utf-8 -*-


class Query:
    def __init__(self, id, rule_pattern, sparql, inter_shape_refs=None):
        self.id = id
        self.rule_pattern = rule_pattern
        self.sparql = sparql
        self.inter_shape_refs = inter_shape_refs

    def get_id(self):
        return self.id

    def get_rule_pattern(self):
        return self.rule_pattern

    def get_SPARQL(self):
        return self.sparql

    def get_inter_shape_refs_names(self):
        return self.inter_shape_refs
