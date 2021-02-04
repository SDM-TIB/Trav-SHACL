package unibz.shapes.shape;

import com.google.common.collect.ImmutableSet;
import unibz.shapes.core.RulePattern;

import java.util.Optional;

public interface Shape {

    String getId();
    Optional<String> getTargetQuery();
    ImmutableSet<ConstraintConjunction> getDisjuncts();

    ImmutableSet<RulePattern> getRulePatterns();
    void computeConstraintQueries(Schema schema, Optional<String> graph);

    ImmutableSet<String> getPredicates();

    ImmutableSet<String> computePredicateSet();

    ImmutableSet<String> getPosShapeRefs();

    ImmutableSet<String> getNegShapeRefs();
}
