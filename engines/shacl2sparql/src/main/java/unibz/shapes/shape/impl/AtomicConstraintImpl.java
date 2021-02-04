package unibz.shapes.shape.impl;

import com.google.common.collect.ImmutableSet;
import unibz.shapes.core.Literal;
import unibz.shapes.core.RulePattern;
import unibz.shapes.core.global.VariableGenerator;
import unibz.shapes.shape.AtomicConstraint;
import unibz.shapes.util.ImmutableCollectors;

import java.util.Optional;
import java.util.stream.IntStream;

import static unibz.shapes.core.global.VariableGenerator.VariableType;

public abstract class AtomicConstraintImpl implements AtomicConstraint {


    private final String id;
    private final Optional<String> datatype;
    private final Optional<String> value;
    private final Optional<String> shapeRef;
    ImmutableSet<String> variables;
    private final boolean isPos;
    private RulePattern rulePattern;

    public AtomicConstraintImpl(String id, Optional<String> datatype, Optional<String> value, Optional<String> shapeRef, boolean isPos) {
        this.id = id;
        this.datatype = datatype;
        this.value = value;
        this.shapeRef = shapeRef;
        this.isPos = isPos;
    }

    public Optional<String> getDatatype() {
        return datatype;
    }

    public Optional<String> getValue() {
        return value;
    }

    public Optional<String> getShapeRef() {
        return shapeRef;
    }

    @Override
    public String getId() {
        return id;
    }

    public boolean isPos() {
        return isPos;
    }

    ImmutableSet<String> generateVariables(VariableType type, Integer numberOfVariables) {

        return IntStream.range(0, numberOfVariables)
                .boxed()
                .map(i -> VariableGenerator.generateVariable(type))
                .collect(ImmutableCollectors.toSet());
    }

    @Override
    public ImmutableSet<String> getVariables() {
        return variables;
    }

    @Override
    public ImmutableSet<Literal> computeRulePatternBody() {
              return shapeRef.isPresent() ?
                        variables.stream()
                                .map(v -> new Literal(
                                        shapeRef.get(),
                                        v,
                                        isPos
                                ))
                                .collect(ImmutableCollectors.toSet()) :
                      ImmutableSet.of();
    }
}
