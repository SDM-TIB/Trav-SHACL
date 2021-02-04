package unibz.shapes.shape;

import com.google.common.collect.ImmutableSet;
import unibz.shapes.core.Query;

import java.util.Optional;
import java.util.stream.Stream;

public interface ConstraintConjunction {

    String getId();

    void computeQueries(Optional<String> graph, boolean includeSPARQLPrefixes);

    Query getMinQuery();

    ImmutableSet<Query> getMaxQueries();

    Stream<String> getPredicates();

    Stream<String> getPosShapeRefs();

    Stream<String> getNegShapeRefs();

    Stream<? extends AtomicConstraint> getConjuncts();
}
