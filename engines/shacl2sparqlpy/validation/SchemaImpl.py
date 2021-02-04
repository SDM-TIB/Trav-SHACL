# -*- coding: utf-8 -*-
from validation.DependencyGraphImpl import DependencyGraphImpl


class SchemaImpl:
    def __init__(self, shapes):
        self.shapes = shapes
        mapped = {}
        for s in shapes:
            mapped[s.getId()] = s
        self.shapeMap = mapped
        self.dependencyGraph = DependencyGraphImpl(self.shapeMap)

    def getShapes(self):
        return self.shapes
