# -*- coding: utf-8 -*-
__author__ = "Philipp D. Rohde"

import json


class SourceDescription:

    class __SourceDescription:
        def __init__(self, filename):
            self.filename = filename
            self.predicates = {}
            self.__read_config()

        @staticmethod
        def __intersection(lst1, lst2):
            """Hybrid method for intersection of two lists. Complexity: O(n)"""
            tmp = set(lst2)
            return [value for value in lst1 if value in tmp]

        def __read_config(self):
            with open(self.filename, 'r', encoding='utf8') as conf:
                self.predicates = json.load(conf)

        def get_classes(self, predicates):
            """Returns for a given list of predicates all classes that have all predicates."""
            classes = []
            for i, pred in enumerate(predicates):
                pred = pred.replace("dbo:", "http://dbpedia.org/ontology/")
                if i == 0:
                    classes.extend(self.predicates[pred])
                else:
                    classes = self.__intersection(classes, self.predicates[pred])
            return classes

    instance = None

    def __new__(cls, filename):
        if not SourceDescription.instance:
            SourceDescription.instance = SourceDescription.__SourceDescription(filename)
        return SourceDescription.instance

    def __getattr__(self, item):
        return getattr(self.instance, item)

    def __setattr__(self, key, value):
        return setattr(self.instance, key, value)
