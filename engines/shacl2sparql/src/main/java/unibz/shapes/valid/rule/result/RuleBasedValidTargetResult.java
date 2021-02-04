package unibz.shapes.valid.rule.result;

import com.google.common.collect.ImmutableSet;
import unibz.shapes.core.Literal;
import unibz.shapes.shape.Shape;
import unibz.shapes.valid.result.ValidTargetResult;
import unibz.shapes.valid.rule.EvalPath;

import java.util.Optional;

public class RuleBasedValidTargetResult extends RuleBasedResult implements ValidTargetResult {

    protected final Optional<Shape> focusShape;

    public RuleBasedValidTargetResult(Literal target, int depth, Optional<Shape> focusShape, ImmutableSet<EvalPath> evalPaths) {
        super(target, depth, evalPaths);
        this.focusShape = focusShape;
    }

    public boolean isProvable() {
        return focusShape.isPresent();
    }

    public Optional<Shape> getFocusShape() {
        return focusShape;
    }
}
