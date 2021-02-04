package unibz.shapes.valid.result;

import com.google.common.collect.ImmutableList;

public interface ResultSet {

    ImmutableList<? extends ValidTargetResult> getValidTargetResults();
    ImmutableList<? extends InvalidTargetResult> getInValidTargetResults();

}
