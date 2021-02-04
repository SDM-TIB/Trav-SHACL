package unibz.shapes.valid.rule;

import com.google.common.collect.ImmutableList;
import unibz.shapes.shape.Shape;
import unibz.shapes.util.ImmutableCollectors;

import java.util.stream.Collectors;
import java.util.stream.Stream;

public class EvalPath {

    private final ImmutableList<Shape> shapes;

    public EvalPath() {
        shapes = ImmutableList.of();
    }

    public EvalPath(Shape shape, EvalPath path) {
        shapes = Stream.concat(
                path.getShapeStream(),
                Stream.of(shape)
        ).collect(ImmutableCollectors.toList());
    }

    private Stream<Shape> getShapeStream() {
        return shapes.stream();
    }

    public ImmutableList<Shape> getShapes() {
        return shapes;
    }

    @Override
    public String toString() {
        return shapes.stream()
                .map(s -> s.getId())
                .collect(Collectors.joining("\n"));
    }
}
