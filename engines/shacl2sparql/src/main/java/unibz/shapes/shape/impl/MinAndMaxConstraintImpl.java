package unibz.shapes.shape.impl;

import unibz.shapes.shape.MinAndMaxConstraint;

import java.util.Optional;

public class MinAndMaxConstraintImpl extends AtomicConstraintImpl implements MinAndMaxConstraint {


    private final String path;
    private final int min;
    private final int max;

    public MinAndMaxConstraintImpl(String id, String path, int min, int max, Optional<String> datatype, Optional<String> value, Optional<String> shapeRef, boolean isPos) {
        super(id, datatype, value, shapeRef, isPos);
        this.path = path;
        this.min = min;
        this.max = max;
    }

    @Override
    public int getMin() {
        return min;
    }

    @Override
    public int getMax() {
        return max;
    }

    @Override
    public String getPath() {
        return path;
    }
}
