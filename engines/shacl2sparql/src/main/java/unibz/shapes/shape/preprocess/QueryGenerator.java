package unibz.shapes.shape.preprocess;

import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableSet;
import unibz.shapes.core.Literal;
import unibz.shapes.core.Query;
import unibz.shapes.core.RulePattern;
import unibz.shapes.core.global.SPARQLPrefixHandler;
import unibz.shapes.core.global.VariableGenerator;
import unibz.shapes.shape.AtomicConstraint;
import unibz.shapes.shape.MaxOnlyConstraint;
import unibz.shapes.shape.NeighborhoodConstraint;
import unibz.shapes.util.ImmutableCollectors;

import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.stream.Collectors;

public class QueryGenerator {
    public static Query generateQuery(String id, ImmutableList<AtomicConstraint> constraints, Optional<String> graph, Optional<String> subquery, boolean includeSPARQLPrefixes) { //@@
        if (constraints.size() > 1 && constraints
                .stream().anyMatch(c -> c instanceof MaxOnlyConstraint)) {
            throw new RuntimeException("Only one max constraint per query is allowed");
        }
        RulePattern rp = computeRulePattern(constraints, id);

        QueryBuilder builder = new QueryBuilder(id, graph, subquery, rp.getVariables());
        constraints.forEach(builder::buildClause);

        return builder.buildQuery(rp, includeSPARQLPrefixes); //@@ added for comparing purposes (Trav-SHACL)
    }

    private static RulePattern computeRulePattern(ImmutableList<AtomicConstraint> constraints, String id) {
        return new RulePattern(
                new Literal(
                        id,
                        VariableGenerator.getFocusNodeVar(),
                        true
                ),
                constraints.stream()
                        .flatMap(c -> c.computeRulePatternBody().stream())
                        .collect(ImmutableCollectors.toSet())
        );
    }

    public static Optional<String> generateLocalSubquery(Optional<String> graphName, ImmutableList<AtomicConstraint> posConstraints) {

        ImmutableList<AtomicConstraint> localPosConstraints = posConstraints.stream()
                .filter(c -> !c.getShapeRef().isPresent())
                .collect(ImmutableCollectors.toList());

        if (localPosConstraints.isEmpty()) {
            return Optional.empty();
        }
        QueryBuilder builder = new QueryBuilder(
                "tmp",
                graphName,
                Optional.empty(),
                ImmutableSet.of(VariableGenerator.getFocusNodeVar())
        );
        localPosConstraints.forEach(builder::buildClause);
        return Optional.of(builder.getSparql(false));
    }

    // mutable
    private static class QueryBuilder {
        List<String> filters;
        List<String> triples;
        private final String id;
        private final Optional<String> subQuery;
        private final Optional<String> graph;
        private final ImmutableSet<String> projectedVariables;

        QueryBuilder(String id, Optional<String> graph, Optional<String> subquery, ImmutableSet<String> projectedVariables) {
            this.id = id;
            this.graph = graph;
            this.projectedVariables = projectedVariables;
            this.filters = new ArrayList<>();
            this.triples = new ArrayList<>();
            subQuery = subquery;
        }

        void addTriple(String path, String object) {
            triples.add(
                    "?" + VariableGenerator.getFocusNodeVar() + " " +
                            path + " " +
                            object + "."
            );
        }

        void addDatatypeFilter(String variable, String datatype, Boolean isPos) {
            String s = getDatatypeFilter(variable, datatype);
            filters.add(
                    (isPos) ?
                            s :
                            "!(" + s + ")"
            );
        }

        void addConstantFilter(String variable, String constant, Boolean isPos) {
            String s = variable + " = " + constant;
            filters.add(
                    (isPos) ?
                            s :
                            "!(" + s + ")"
            );
        }

        private String getDatatypeFilter(String variable, String datatype) {
            return "datatype(?" + variable + ") = " + datatype;
        }

        String getSparql(boolean includePrefixes) {
            return (includePrefixes ?
                    SPARQLPrefixHandler.getPrefixString() :
                    "") +
                    getProjectionString() +
                    " WHERE{" +
                    (graph.map(s -> "\nGRAPH " + s + "{").orElse("")
                    ) +
                    "\n\n" +
                    getTriplePatterns() +
                    "\n" +
                    (subQuery.isPresent() ?
                            "{\n" + subQuery.get() + "\n}\n" :
                            ""
                    ) +
                    (graph.isPresent() ?
                            "\n}" :
                            ""
                    ) +
                    "\n}" +
                    (includePrefixes ? " ORDER BY ?" + VariableGenerator.getFocusNodeVar() : ""); //@@ added for comparing purposes (Trav-SHACL)
        }

        private String getProjectionString() {
            return "SELECT DISTINCT " +
                    projectedVariables.stream()
                            .map(v -> "?" + v)
                            .collect(Collectors.joining(", "));
        }

        String getTriplePatterns() {
            String tripleString = triples.stream()
                    .collect(Collectors.joining("\n"));

            if (filters.isEmpty()) {
                return tripleString;
            }
            return tripleString +
                    generateFilterString();
        }

        private String generateFilterString() {
            if (filters.isEmpty()) {
                return "";
            }
            return "\nFILTER(\n" +
                    (filters.size() == 1 ?
                            filters.iterator().next() :
                            filters.stream()
                                    .collect(Collectors.joining(" AND\n"))
                    )
                    + ")";
        }

        void addCardinalityFilter(ImmutableSet<String> variables) {
            ImmutableList<String> list = ImmutableList.copyOf(variables);
            for (int i = 0; i < list.size(); i++) {
                for (int j = i + 1; j < list.size(); j++) {
                    filters.add("?" + list.get(i) + " != ?" + list.get(j));
                }
            }
        }

        private void buildClause(AtomicConstraint c) {

            ImmutableSet<String> variables = c.getVariables();

            if (c instanceof NeighborhoodConstraint) {
                String path = ((NeighborhoodConstraint) c).getPath();

                if (c.getValue().isPresent()) {
                    addTriple(path, c.getValue().get());
                    return;
                }
                variables.forEach(v -> addTriple(path, "?" + v));
            } else if (c.getValue().isPresent()) {
                addConstantFilter(
                        variables.iterator().next(),
                        c.getValue().get(),
                        c.isPos()
                );
            }

            if (c.getDatatype().isPresent()) {
                variables.forEach(v -> addDatatypeFilter(
                        v,
                        c.getDatatype().get(),
                        c.isPos()
                ));
            }

            if (variables.size() > 1) {
                addCardinalityFilter(variables);
            }
        }

        Query buildQuery(RulePattern rulePattern, boolean includeSPARQLPrefixes) { //@@ added for comparing purposes (Trav-SHACL)
            return new Query(
                    id,
                    rulePattern,
                    getSparql(includeSPARQLPrefixes) //@@
            );
        }
    }
}

