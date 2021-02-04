package unibz.shapes.shape.impl;

import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableMap;
import com.google.common.collect.ImmutableSet;
import unibz.shapes.shape.DependencyGraph;
import unibz.shapes.shape.Shape;
import unibz.shapes.util.ImmutableCollectors;

import java.util.stream.Stream;

public class DependencyGraphImpl implements DependencyGraph {


    /** Maps a shape to an array of 2 sets:
            first set: positive shape references
            second set: negative shape references */

    ImmutableMap<Shape, ImmutableList<ImmutableSet<Shape>>> references;

    public DependencyGraphImpl(ImmutableMap<Shape, ImmutableList<ImmutableSet<Shape>>> references) {
        this.references = references;
    }

    @Override
    public Stream<Shape> getPosReferences(Shape shape) {
        return references.get(shape).get(0).stream();
    }

    @Override
    public Stream<Shape> getNegReferences(Shape shape) {
        return references.get(shape).get(1).stream();
    }

    @Override
    public Stream<Shape> getAllReferences(Shape shape) {
        return  Stream.concat(
                getPosReferences(shape),
                getNegReferences(shape)
        );
    }

    static DependencyGraph computeDependencyGraph(ImmutableMap<String, Shape> shapeMap) {
        return new DependencyGraphImpl(shapeMap.values().stream()
                .collect(ImmutableCollectors.toMap(
                        e -> e,
                        e -> getShapeRefs(e, shapeMap)
                )));
    }

    static ImmutableList<ImmutableSet<Shape>> getShapeRefs(Shape shape, ImmutableMap<String, Shape> shapeMap) {
        return ImmutableList.of(
                getPosShapeRefs(shape, shapeMap),
                getNegShapeRefs(shape, shapeMap)
        );
    }

    private static ImmutableSet<Shape> getPosShapeRefs(Shape shape, ImmutableMap<String, Shape> shapeMap) {
        return shape.getPosShapeRefs().stream()
                .map(r -> shapeMap.get(r))
                .collect(ImmutableCollectors.toSet());

    }

    private static ImmutableSet<Shape> getNegShapeRefs(Shape shape, ImmutableMap<String, Shape> shapeMap) {
        return shape.getNegShapeRefs().stream()
                .map(r -> shapeMap.get(r))
                .collect(ImmutableCollectors.toSet());
    }
}
