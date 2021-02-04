package unibz.shapes.shape.impl;

import com.google.common.collect.ImmutableSet;
import unibz.shapes.core.global.VariableGenerator;
import unibz.shapes.shape.MaxOnlyConstraint;

import java.util.Optional;

public class MaxOnlyConstraintImpl extends AtomicConstraintImpl implements MaxOnlyConstraint {


    private final String path;
    private final int max;

    public MaxOnlyConstraintImpl(String id, String path, int max, Optional<String> datatype, Optional<String> value, Optional<String> shapeRef, boolean isPos) {
        super(id, datatype, value, shapeRef, isPos);
        this.path = path;
        this.max = max;
        this.variables = computeVariables();
    }

    private ImmutableSet<String> computeVariables() {
        return generateVariables(VariableGenerator.VariableType.VALIDATION, max + 1);
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
