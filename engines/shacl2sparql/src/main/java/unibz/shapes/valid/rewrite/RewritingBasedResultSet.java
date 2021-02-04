package unibz.shapes.valid.rewrite;

import com.google.common.collect.ImmutableList;
import unibz.shapes.valid.result.InvalidTargetResult;
import unibz.shapes.valid.result.ResultSet;
import unibz.shapes.valid.result.ValidTargetResult;

public class RewritingBasedResultSet implements ResultSet {
    @Override
    public ImmutableList<? extends ValidTargetResult> getValidTargetResults() {
        throw new RuntimeException("TODO: implement");
    }

    @Override
    public ImmutableList<? extends InvalidTargetResult> getInValidTargetResults() {
        throw new RuntimeException("TODO: implement");
    }
}
