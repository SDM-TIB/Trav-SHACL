package unibz.shapes.shape.impl;

import com.google.common.collect.ImmutableSet;
import unibz.shapes.core.Literal;
import unibz.shapes.core.RulePattern;
import unibz.shapes.core.global.VariableGenerator;
import unibz.shapes.shape.ConstraintConjunction;
import unibz.shapes.shape.Schema;
import unibz.shapes.shape.Shape;
import unibz.shapes.shape.preprocess.ShapeParser;
import unibz.shapes.util.ImmutableCollectors;

import java.util.Objects;
import java.util.Optional;
import java.util.stream.Collectors;
import java.util.stream.Stream;

public class ShapeImpl implements Shape {
    private final String id;
    private final Optional<String> targetQuery;
    private final ImmutableSet<ConstraintConjunction> disjuncts;
    private final boolean includeSPARQLPrefixes; //@@ added for comparing purposes (Trav-SHACL)
    private ImmutableSet<RulePattern> rulePatterns;
    private ImmutableSet<String> predicates;

    public ShapeImpl(String id, Optional<String> targetQuery, ImmutableSet<ConstraintConjunction> disjuncts, boolean includeSPARQLPrefixes) { //@@
        this.id = id;
        this.targetQuery = targetQuery;
        this.disjuncts = disjuncts;
        this.includeSPARQLPrefixes = includeSPARQLPrefixes; //@@
        computePredicateSet();
    }

    public String getId() {
        return id;
    }

    public Optional<String> getTargetQuery() {
        return targetQuery;
    }

    @Override
    public ImmutableSet<ConstraintConjunction> getDisjuncts() {
        return disjuncts;
    }

    @Override
    public ImmutableSet<RulePattern> getRulePatterns() {
        return rulePatterns;
    }

    @Override
    public void computeConstraintQueries(Schema schema, Optional<String> graph) {
        disjuncts.forEach(c -> c.computeQueries(graph, includeSPARQLPrefixes)); //@@
        this.rulePatterns = computeRulePatterns();
    }

    @Override
    public ImmutableSet<String> getPredicates() {
        return predicates;
    }

    @Override
    public ImmutableSet<String> computePredicateSet() {
        this.predicates = Stream.concat(
                Stream.of(id),
                disjuncts.stream()
                        .flatMap(d -> d.getPredicates())
        ).collect(ImmutableCollectors.toSet());
        return predicates;
    }

    @Override
    public ImmutableSet<String> getPosShapeRefs() {
        return disjuncts.stream()
                .flatMap(d -> d.getPosShapeRefs())
                .collect(ImmutableCollectors.toSet());
    }

    @Override
    public ImmutableSet<String> getNegShapeRefs() {
        return disjuncts.stream()
                .flatMap(d -> d.getNegShapeRefs())
                .collect(ImmutableCollectors.toSet());
    }

    private ImmutableSet<RulePattern> computeRulePatterns() {
        String focusNodeVar = VariableGenerator.getFocusNodeVar();
        Literal head = new Literal(id, focusNodeVar, true);
        return disjuncts.stream()
                .map(d -> new RulePattern(
                        head,
                        getDisjunctRPBody(d)
                ))
                .collect(ImmutableCollectors.toSet());
    }

    private ImmutableSet<Literal> getDisjunctRPBody(ConstraintConjunction d) {
        String focusNodeVar = VariableGenerator.getFocusNodeVar();
        return Stream.concat(
                Stream.of(
                        new Literal(
                                d.getMinQuery().getId(),
                                focusNodeVar,
                                true
                        )),
                d.getMaxQueries().stream()
                        .map(q -> q.getId())
                        .map(s -> new Literal(
                                s,
                                focusNodeVar,
                                false
                        ))
        ).collect(ImmutableCollectors.toSet());
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        ShapeImpl shape = (ShapeImpl) o;
        return id.equals(shape.id);
    }

    @Override
    public int hashCode() {
        return Objects.hash(id);
    }

    @Override
    public String toString() {
        return id;
    }
}
