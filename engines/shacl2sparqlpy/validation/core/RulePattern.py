# -*- coding: utf-8 -*-
from validation.core.Literal import Literal

class RulePattern:
    # If a value for each variable is produced (by a solution mapping), then the rule pattern can be instantiated.
    # Note that it may be the case that these variables do not appear in the the body of the rule (because there is no constraint to propagate on these values, they only need to exist)

    def __init__(self, head, body):
        self.head = head
        self.literals = body

        # print("Rule Pattern - head: ", head.getPredicate(), " ", head.getArg(), " body: ", str([b.getPredicate() + " " + b.getArg() + " " + str(b.getIsPos()) for b in body]))

        self.variables = set([head.getArg()] + [a.getArg() for a in body if a is not None])

    def getHead(self):
        return self.head

    def getBody(self):
        return self.literals

    def instantiateAtom(self, a, bs):
        # given a binding with many possible projected variables, returns the atom that matches the variable
        return Literal(
                a.getPredicate(),
                bs[a.getArg()]["value"],  # arg instance, e.g., http://dbpedia.org/resource/Titanic_(1953_film),
                a.getIsPos()
        )

    def instantiateBody(self, bs):
        return frozenset({self.instantiateAtom(a, bs) for a in self.literals})

    def getVariables(self):
        return self.variables