package unibz.shapes.shape.impl;

import com.google.common.collect.ImmutableMap;
import com.google.common.collect.ImmutableSet;
import unibz.shapes.shape.DependencyGraph;
import unibz.shapes.shape.Schema;
import unibz.shapes.shape.Shape;
import unibz.shapes.util.ImmutableCollectors;

import java.util.Optional;

public class SchemaImpl implements Schema {

    private final ImmutableMap<String, Shape> shapeMap;
    private final DependencyGraph dependencyGraph;

    public SchemaImpl(ImmutableSet<Shape> shapes) {

        this.shapeMap = shapes.stream()
                .collect(ImmutableCollectors.toMap(
                        Shape::getId,
                        s -> s
                ));
        dependencyGraph = DependencyGraphImpl.computeDependencyGraph(shapeMap);
    }

    @Override
    public Shape getShape(String name) {
        Shape s = shapeMap.get(name);
        return s;
    }

    @Override
    public ImmutableSet<Shape> getShapes() {
        return ImmutableSet.copyOf(shapeMap.values());
    }

    @Override
    public ImmutableSet<Shape> getShapesReferencedBy(Shape s) {
        return dependencyGraph.getAllReferences(s)
                .collect(ImmutableCollectors.toSet());
    }
}
