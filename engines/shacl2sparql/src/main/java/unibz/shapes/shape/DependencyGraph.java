package unibz.shapes.shape;

import java.util.stream.Stream;

public interface DependencyGraph {

    Stream<Shape> getPosReferences(Shape shape);

    Stream<Shape> getNegReferences(Shape shape);

    Stream<Shape> getAllReferences(Shape shape);
}
