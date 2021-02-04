package unibz.shapes.shape.impl;

import com.google.common.collect.ImmutableSet;
import unibz.shapes.core.global.VariableGenerator;
import unibz.shapes.shape.MinOnlyConstraint;

import java.util.Optional;

public class MinOnlyConstraintImpl extends AtomicConstraintImpl implements MinOnlyConstraint {


    private final String path;
    private final int min;

    public MinOnlyConstraintImpl(String id, String path, int min, Optional<String> datatype, Optional<String> value, Optional<String> shapeRef, boolean isPos) {
        super(id, datatype, value, shapeRef, isPos);
        this.path = path;
        this.min = min;
        this.variables = computeVariables();
    }

    private ImmutableSet<String> computeVariables() {
        return generateVariables(VariableGenerator.VariableType.VALIDATION, min);
    }

    @Override
    public int getMin() {
        return min;
    }

    @Override
    public String getPath() {
        return path;
    }
}
