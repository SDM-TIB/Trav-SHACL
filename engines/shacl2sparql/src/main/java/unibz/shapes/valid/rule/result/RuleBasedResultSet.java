package unibz.shapes.valid.rule.result;

import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableSet;
import unibz.shapes.core.Literal;
import unibz.shapes.shape.Shape;
import unibz.shapes.valid.result.ResultSet;
import unibz.shapes.valid.rule.EvalPath;

import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.stream.Collectors;

public class RuleBasedResultSet implements ResultSet {


    // Implemented as lists for efficiency.
    // The implementation of evaluation should guarantee that there is no duplicate
    private List<RuleBasedValidTargetResult> validTargetResults;
    private List<RuleBasedInvalidTargetResult> invalidTargetResults;

    public RuleBasedResultSet() {
        this.validTargetResults = new ArrayList<>();
        this.invalidTargetResults = new ArrayList<>();
    }

    public void registerValidTarget(Literal target, int depth, Optional<Shape> focusShape, ImmutableSet<EvalPath> evalPaths){
        validTargetResults.add(new RuleBasedValidTargetResult(target, depth, focusShape, evalPaths));
    }

    public void registerInvalidTarget(Literal target, int depth, Shape focusShape, ImmutableSet<EvalPath> evalPaths){
        invalidTargetResults.add(new RuleBasedInvalidTargetResult(target, depth, focusShape, evalPaths));
    }

    public ImmutableList<RuleBasedValidTargetResult> getValidTargetResults(){
        return ImmutableList.copyOf(validTargetResults);
    }
    public ImmutableList<RuleBasedInvalidTargetResult> getInValidTargetResults(){
        return ImmutableList.copyOf(invalidTargetResults);
    }

    @Override
    public String toString() {
        return invalidTargetResults.stream()
                .map(r -> r.toString())
                .collect(Collectors.joining("\n"));
    }
}
