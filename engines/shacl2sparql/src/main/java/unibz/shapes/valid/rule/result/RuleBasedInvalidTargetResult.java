package unibz.shapes.valid.rule.result;

import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableSet;
import unibz.shapes.core.Literal;
import unibz.shapes.shape.Shape;
import unibz.shapes.util.ImmutableCollectors;
import unibz.shapes.valid.result.InvalidTargetResult;
import unibz.shapes.valid.rule.EvalPath;

import java.util.stream.Stream;

public class RuleBasedInvalidTargetResult extends RuleBasedResult implements InvalidTargetResult {

    private final Shape focusShape;

    public RuleBasedInvalidTargetResult(Literal target, int depth, Shape focusShape, ImmutableSet<EvalPath> evalPaths) {
        super(target, depth, evalPaths);
        this.focusShape = focusShape;
    }

    public Shape getFocusShape() {
        return focusShape;
    }

    @Override
    public String toString() {
        return getTarget() +
                ", violated at depth "+
                getDepth()+
                ", focus shape: "+
                getFocusShape()+
                ", path: "+
                displayFirstEvalpath();
    }

    private String displayFirstEvalpath() {
        EvalPath path = evalPaths.iterator().next();

        return path.getShapes().size() == 0?
                focusShape.toString():
                focusShape + " -> "+path.toString();
    }
}
