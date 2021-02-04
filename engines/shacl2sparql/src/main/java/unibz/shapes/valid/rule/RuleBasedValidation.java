package unibz.shapes.valid.rule;

import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableSet;
import org.eclipse.rdf4j.query.BindingSet;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import unibz.shapes.core.Literal;
import unibz.shapes.core.Query;
import unibz.shapes.core.RulePattern;
import unibz.shapes.core.global.RuleMap;
import unibz.shapes.endpoint.QueryEvaluation;
import unibz.shapes.endpoint.SPARQLEndpoint;
import unibz.shapes.shape.ConstraintConjunction;
import unibz.shapes.shape.Schema;
import unibz.shapes.shape.Shape;
import unibz.shapes.util.ImmutableCollectors;
import unibz.shapes.util.Output;
import unibz.shapes.valid.result.ResultSet;
import unibz.shapes.valid.Validation;
import unibz.shapes.valid.rule.result.RuleBasedResultSet;

import java.io.IOException;
import java.time.Duration;
import java.time.Instant;
import java.util.*;
import java.util.stream.Collectors;

public class RuleBasedValidation implements Validation {

    private static Logger log = (Logger) LoggerFactory.getLogger(RuleBasedValidation.class);

    private final SPARQLEndpoint endpoint;
    private final Schema schema;
    private final ImmutableSet<Shape> targetShapes;
    private final ImmutableSet<String> targetShapePredicates;
    private final Output logOutput;
    private final Output validTargetsOuput;
    private final Output invalidTargetsOuput;
    private final Output statsOutput;
    private final RuleBasedValidStats stats;
    private final RuleBasedResultSet resultSet;

    //@@ added for comparison purposes (Trav-SHACL)
    private final Output tracesOutput;
    Set<String> validsLog = new HashSet<>();
    Set<String> invalidsLog = new HashSet<>();
    Set<String> tracesLog = new HashSet<>();
    Instant startMeasureContBehavior;
    int tracesCount = 0;

    public RuleBasedValidation(SPARQLEndpoint endpoint, Schema schema, Output logOutput, Output validTargetsOuput, Output invalidTargetsOuput, Output statsOuput, Output tracesOutput) {  //@@
        this.endpoint = endpoint;
        this.schema = schema;
        this.validTargetsOuput = validTargetsOuput;
        this.invalidTargetsOuput = invalidTargetsOuput;
        this.logOutput = logOutput;
        targetShapes = extractTargetShapes();
        targetShapePredicates = targetShapes.stream()
                .map(Shape::getId)
                .collect(ImmutableCollectors.toSet());
        this.stats = new RuleBasedValidStats();
        this.resultSet = new RuleBasedResultSet();
        statsOutput = statsOuput;
        this.tracesOutput = tracesOutput;  //@@ added for comparison purposes (Trav-SHACL)
        tracesOutput.write("Target, #TripleInThatClass, TimeSinceStartOfVerification(ms)");  //@@
    }

    public ResultSet exec() {
        Instant start = Instant.now();
        startMeasureContBehavior = start;  //@@ added for comparison purposes (Trav-SHACL)
        logOutput.write("Retrieving targets ...");
        Set<Literal> targets = extractTargetAtoms();
        logOutput.write("\nTargets retrieved.");
        logOutput.write("Number of targets:\n" + targets.size());
        stats.recordInitialTargets(targets.size());
        validate(
                0,
                EvalState.init(targetShapes, targets),
                targetShapes
        );
        Instant finish = Instant.now();
        long elapsed = Duration.between(start, finish).toMillis();
        stats.recordTotalTime(elapsed);
        log.info("Total execution time: " + elapsed);
        logOutput.write("\nMaximal number or rules in memory: " + stats.maxRuleNumber);
        stats.writeAll(statsOutput);
        writeTargetsToFile();  //@@ added for comparison purposes (Trav-SHACL)

        try {
            logOutput.close();
            validTargetsOuput.close();
            invalidTargetsOuput.close();
            statsOutput.close();
            tracesOutput.close();  //@@
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
        return resultSet;
    }

    private Set<Literal> extractTargetAtoms() {
        return targetShapes.stream()
                .filter(s -> s.getTargetQuery().isPresent())
                .flatMap(s -> extractTargetAtoms(s, s.getTargetQuery().get()).stream())
                .collect(Collectors.toSet());
    }

    private Set<Literal> extractTargetAtoms(Shape shape, String targetQuery) {
        logOutput.start("Evaluating query:\n" + targetQuery);
        QueryEvaluation eval = endpoint.runQuery(
                shape.getId(),
                targetQuery
        );
        logOutput.elapsed();
        return eval.getBindingSets().stream()
                .map(b -> b.getBinding("x").getValue().stringValue())
                .map(i -> new Literal(shape.getId(), i, true))
                .collect(Collectors.toSet());
    }

    private ImmutableSet<Shape> extractTargetShapes() {
        return schema.getShapes().stream()
                .filter(s -> s.getTargetQuery().isPresent())
                .collect(ImmutableCollectors.toSet());
    }

    private void validate(int depth, EvalState state, ImmutableSet<Shape> focusShapes) {

        // termination condition 1: all targets are validated/violated
        if (state.remainingTargets.isEmpty()) {
            return;
        }

        // termination condition 2: all shapes have been visited
        if (state.visitedShapes.size() == schema.getShapes().size()) {
            state.remainingTargets.forEach(t -> registerTarget(t, true, depth, state, "not violated after termination", Optional.empty()));
            return;
        }

        logOutput.start("Starting validation at depth :" + depth);

        validateFocusShapes(state, focusShapes, depth);

        validate(depth + 1, state, updateFocusShapes(state, focusShapes));
    }

    //@@ added for comparison purposes (Trav-SHACL)
    public void writeTargetsToFile() {
        Iterator<String> itValids = validsLog.iterator();
        while(itValids.hasNext()) {
            validTargetsOuput.write(itValids.next());
        }

        Iterator<String> itInvalids = invalidsLog.iterator();
        while(itInvalids.hasNext()) {
            invalidTargetsOuput.write(itInvalids.next());
        }

        Iterator<String> itTraces = tracesLog.iterator();
        while(itTraces.hasNext()) {
            tracesOutput.write(itTraces.next());
        }
    }

    private void registerTarget(Literal t, boolean isValid, int depth, EvalState state, String logMessage, Optional<Shape> focusShape) {
        String log = t.toString() +
                ", depth " + depth +
                (focusShape.map(shape -> ", focus shape " + shape).orElse("")) +
                ", " + logMessage;
        ImmutableSet<EvalPath> evalPaths;
        String targetType;
        if (isValid) {
            targetType = "valid";
            //validTargetsOuput.write(log);
            validsLog.add(log);
            evalPaths = focusShape.isPresent()?
                    state.getEvalPaths(focusShape.get()):
                    ImmutableSet.of();
            resultSet.registerValidTarget(t,depth, focusShape, evalPaths);
        } else {
            targetType = "violated";
            //invalidTargetsOuput.write(log);
            invalidsLog.add(log);
            Shape shape = focusShape.orElseThrow(
                    () -> new RuntimeException("A violation result must have a focus shape"));
            resultSet.registerInvalidTarget(t, depth, shape, state.getEvalPaths(shape));
        }

        //@@ added for comparison purposes (Trav-SHACL)
        Instant finish = Instant.now();
        long elapsed = Duration.between(startMeasureContBehavior, finish).toMillis();
        String logTrace = targetType + ", " + tracesCount + ", " + elapsed;
        tracesLog.add(logTrace);
        tracesCount = tracesCount + 1;
    }

    private ImmutableSet<Shape> updateFocusShapes(EvalState state, ImmutableSet<Shape> focusShapes) {

        ImmutableSet<String> bodyAtomsPred = state.ruleMap.getAllBodyAtoms()
                .map(a -> a.getPredicate())
                .collect(ImmutableCollectors.toSet());

        focusShapes.forEach(s ->
                state.updateEvalPathMap(
                        s,
                        filterReferencedShapes(s, schema, state, bodyAtomsPred)
                ));

        return state.getFocusShapes();
    }

    private ImmutableSet<Shape> filterReferencedShapes(Shape shape, Schema schema, EvalState state, ImmutableSet<String> bodyAtomsPred) {
        return schema.getShapesReferencedBy(shape).stream()
                .filter(s -> !state.visitedShapes.contains(s))
                .filter(s -> bodyAtomsPred.contains(s.getId()))
                .collect(ImmutableCollectors.toSet());
    }

    private void saturate(EvalState state, int depth, Shape s) {
        boolean negated = negateUnMatchableHeads(state, depth, s);
        boolean inferred = applyRules(state, depth, s);
        if (negated || inferred) {
            saturate(state, depth, s);
        }
    }

    private boolean applyRules(EvalState state, int depth, Shape s) {
        RuleMap retainedRules = new RuleMap();
        ImmutableList<Literal> freshLiterals = state.ruleMap.entrySet().stream()
                .map(e -> applyRules(e.getKey(), e.getValue(), state, retainedRules))
                .filter(Optional::isPresent)
                .map(Optional::get)
                .collect(ImmutableCollectors.toList());
        state.ruleMap = retainedRules;
        state.assignment.addAll(freshLiterals);
        if (freshLiterals.isEmpty()) {
            return false;
        }

        ImmutableSet<Literal> candidateValidTargets = freshLiterals.stream()
                .filter(a -> targetShapePredicates.contains(a.getPredicate()))
                .collect(ImmutableCollectors.toSet());

        Map<Boolean, List<Literal>> part1 = state.remainingTargets.stream()
                .collect(Collectors.partitioningBy(candidateValidTargets::contains));

        state.remainingTargets = ImmutableSet.copyOf(part1.get(false));

//        stats.recordDecidedTargets(part1.get(true).size());

        Map<Boolean, List<Literal>> part2 = part1.get(true).stream()
                .collect(Collectors.partitioningBy(Literal::isPos));

        state.validTargets.addAll(part2.get(true));
        state.invalidTargets.addAll(part2.get(false));
        part2.get(true).forEach(t ->
                registerTarget(t, true, depth, state, "", Optional.of(s))
        );
        part2.get(false).forEach(t ->
                registerTarget(t, false, depth, state, "", Optional.of(s))
        );
        logOutput.write("Remaining targets :" + state.remainingTargets.size());
        return true;
    }

    private Optional<Literal> applyRules(Literal head, Set<ImmutableSet<Literal>> bodies, EvalState state, RuleMap retainedRules) {
        Set<ImmutableSet<Literal>> validBodies = new HashSet<>();
        if (bodies.stream()
                .map(b -> applyRule(head, b, state, validBodies))
                .filter(result -> result == true).count() > 0) { // if any invalid body rule
            return Optional.of(head);
        } else {
            for (ImmutableSet body : validBodies) {  // changed to avoid short-circuit operation
                retainedRules.addRule(head, body);
            }
            return Optional.empty();
        }
    }

    private boolean applyRule(Literal head, ImmutableSet<Literal> body, EvalState state, Set<ImmutableSet<Literal>> validBodies) {
        if (state.assignment.containsAll(body)) {
            return true;
        }
        if (body.stream()
                .noneMatch(a -> state.assignment.contains(a.getNegation()))) {
            validBodies.add(body);  // changed to avoid short-circuit operation
        }
        return false;
    }

    private void validateFocusShapes(EvalState state, ImmutableSet<Shape> focusShapes, int depth) {
        focusShapes.forEach(s -> evalShape(state, s, depth));
    }

    private void evalShape(EvalState state, Shape s, int depth) {
        logOutput.write("evaluating queries for shape " + s.getId());
        s.getDisjuncts().forEach(d -> evalDisjunct(state, d, s));
        state.evaluatedPredicates.addAll(s.getPredicates());
        state.addVisitedShape(s);
        saveRuleNumber(state);

        logOutput.start("saturation ...");
        saturate(state, depth, s);
        stats.recordSaturationTime(logOutput.elapsed());

        logOutput.write("\nvalid targets: " + state.validTargets.size());
        logOutput.write("\nInvalid targets: " + state.invalidTargets.size());
        logOutput.write("\nRemaining targets: " + state.remainingTargets.size());
    }

    private void saveRuleNumber(EvalState state) {
        int ruleNumber = state.ruleMap.getRuleNumber();
        logOutput.write("Number of rules " + ruleNumber);
        stats.recordNumberOfRules(ruleNumber);
    }

    private void evalDisjunct(EvalState state, ConstraintConjunction d, Shape s) {
        evalQuery(state, d.getMinQuery(), s);
        d.getMaxQueries()
                .forEach(q -> evalQuery(state, q, s));
    }

    private void evalQuery(EvalState state, Query q, Shape s) {
        logOutput.start("Evaluating query:\n" + q.getSparql());
        QueryEvaluation eval = endpoint.runQuery(q.getId(), q.getSparql());
        stats.recordQueryExecTime(logOutput.elapsed());
        logOutput.write("Number of solution mappings: " + eval.getBindingSets().size());
        stats.recordNumberOfSolutionMappings(eval.getBindingSets().size());
        stats.recordQuery();
        logOutput.start("Grounding rules ...");
        eval.getBindingSets().forEach(
                b -> evalBindingSet(state, b, q.getRulePattern(), s.getRulePatterns())
        );
        stats.recordGroundingTime(logOutput.elapsed());
    }

    private void evalBindingSet(EvalState state, BindingSet bs, RulePattern queryRP, ImmutableSet<RulePattern> shapeRPs) {
        evalBindingSet(state, bs, queryRP);
        shapeRPs.forEach(p -> evalBindingSet(state, bs, p));

    }

    private void evalBindingSet(EvalState state, BindingSet bs, RulePattern pattern) {
        Set<String> bindingVars = bs.getBindingNames();
        if (bindingVars.containsAll(pattern.getVariables())) {
            state.ruleMap.addRule(
                    pattern.instantiateAtom(pattern.getHead(), bs),
                    pattern.instantiateBody(bs)
            );
        }
    }

    private boolean negateUnMatchableHeads(EvalState state, int depth, Shape s) {
        Set<Literal> ruleHeads = state.ruleMap.keySet();

        int initialAssignmentSize = state.assignment.size();

        // first negate unmatchable body atoms
        state.ruleMap.getAllBodyAtoms().
                filter(a -> !isSatisfiable(a, state, ruleHeads))
                .map(this::getNegatedAtom)
                .forEach(a -> state.assignment.add(a));

        // then negate unmatchable targets
        Map<Boolean, List<Literal>> part2 = state.remainingTargets.stream().
                collect(Collectors.partitioningBy(
                        a -> isSatisfiable(a, state, ruleHeads)
                ));
        List<Literal> inValidTargets = part2.get(false);
        state.invalidTargets.addAll(inValidTargets);

        inValidTargets.forEach(t ->
                registerTarget(t, false, depth, state, "", Optional.of(s))
        );

        state.assignment.addAll(
                inValidTargets.stream()
                        .map(Literal::getNegation)
                        .collect(ImmutableCollectors.toSet())
        );
        state.remainingTargets = new HashSet<>(part2.get(true));

        return initialAssignmentSize != state.assignment.size();
    }

    private Literal getNegatedAtom(Literal a) {
        return a.isPos() ?
                a.getNegation() :
                a;
    }

    private boolean isSatisfiable(Literal a, EvalState state, Set<Literal> ruleHeads) {
        return (!state.evaluatedPredicates.contains(a.getPredicate())) || ruleHeads.contains(a.getAtom()) || state.assignment.contains(a);
    }


    private static class EvalState {

        private Set<Shape> visitedShapes;
        private Set<String> evaluatedPredicates;

        RuleMap ruleMap;
        Set<Literal> remainingTargets;
        Set<Literal> validTargets;
        Set<Literal> invalidTargets;
        Set<Literal> assignment;

        //Map from shape name to a set of evaluation paths
        Map<Shape, ImmutableSet<EvalPath>> evalPathsMap;

        static EvalState init(ImmutableSet<Shape> targetShapes, Set<Literal> targets) {
            return new EvalState(
                    targets,
                    new RuleMap(),
                    new HashSet<>(),
                    new HashSet<>(),
                    new HashSet<>(),
                    new HashSet<>(),
                    new HashSet<>(),
                    targetShapes.stream()
                            .collect(Collectors.toMap(
                                    s -> s,
                                    s -> ImmutableSet.of(
                                            new EvalPath()
                                    )
                            ))
            );
        }

        private EvalState(Set<Literal> targetLiterals, RuleMap ruleMap, Set<Literal> assignment, Set<Shape> visitedShapes,
                          Set<String> evaluatedPredicates, Set<Literal> validTargets, Set<Literal> invalidTargets, Map<Shape, ImmutableSet<EvalPath>> evalPathsMap) {
            this.remainingTargets = targetLiterals;
            this.ruleMap = ruleMap;
            this.assignment = assignment;
            this.visitedShapes = visitedShapes;
            this.evaluatedPredicates = evaluatedPredicates;
            this.validTargets = validTargets;
            this.invalidTargets = invalidTargets;
            this.evalPathsMap = evalPathsMap;
        }

        void addVisitedShape(Shape shape) {
            visitedShapes.add(shape);
        }

        void addEvaluatedPredicates(ImmutableSet<String> predicates) {
            evaluatedPredicates.addAll(predicates);
        }

        public void updateEvalPathMap(Shape shape, ImmutableSet<Shape> referencedShapes) {
            if (!evalPathsMap.containsKey(shape))
                throw new RuntimeException("Shape " + shape.getId() + " should have a (possibly empty) set of evaluation paths");
            ImmutableSet<EvalPath> paths = evalPathsMap.get(shape);
            evalPathsMap.remove(shape);
            referencedShapes.forEach(s ->
                    evalPathsMap.put(
                            s,
                            extendEvalPathSet(
                                    s,
                                    paths
                            )));
        }

        private ImmutableSet<EvalPath> extendEvalPathSet(Shape s, ImmutableSet<EvalPath> paths) {
            return paths.stream()
                    .map(p -> new EvalPath(s, p))
                    .collect(ImmutableCollectors.toSet());
        }

        ImmutableSet<EvalPath> getEvalPaths(Shape shape) {
            return evalPathsMap.get(shape);
        }

        ImmutableSet<Shape> getFocusShapes() {
            return ImmutableSet.copyOf(evalPathsMap.keySet());
        }
    }
}
