# -*- coding: utf-8 -*-


class DependencyGraphImpl:
    """ Maps a shape to an array of 2 sets:
            first set: positive shape references
            second set: negative shape references """

    def __init__(self, shapeMap):
        # e.g., {ActorShape = [[], []], MovieShape = [[ActorShape], []]}

        self.references = self.computeDependencyGraph(shapeMap)

    def computeDependencyGraph(self, shapeMap):
        references = {}
        for shape in shapeMap:
            references[shape] = self.getShapeRefs(shapeMap[shape], shapeMap)
        print("references", references)
        return references

    def getShapeRefs(self, shape, shapeMap):
        return [self.getPosShapeRefs(shape, shapeMap), self.getNegShapeRefs(shape, shapeMap)]

    def getPosShapeRefs(self, shape, shapeMap):
        return [shapeMap.get(r) for r in shape.getPosShapeRefs()[0] if shapeMap.get(r) is not None]

    def getNegShapeRefs(self, shape, shapeMap):
        return [shapeMap.get(r) for r in shape.getNegShapeRefs()[0] if shapeMap.get(r) is not None]