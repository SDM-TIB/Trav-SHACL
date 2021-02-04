package unibz.shapes.valid.rule.result;

import com.google.common.collect.ImmutableSet;
import unibz.shapes.core.Literal;
import unibz.shapes.valid.rule.EvalPath;

abstract class RuleBasedResult {

    protected final Literal target;
    protected final ImmutableSet<EvalPath> evalPaths;
    protected final int depth;

    public RuleBasedResult(Literal target, int depth, ImmutableSet<EvalPath> evalPaths){
        this.target = target;
        this.evalPaths = evalPaths;
        this.depth = depth;
    }

    public Literal getTarget() {
        return target;
    }

    public ImmutableSet<EvalPath> getEvalPaths() {
        return evalPaths;
    }

    public int getDepth() {
        return depth;
    }

}
