# -*- coding: utf-8 -*-
from validation.utils import fileManagement
from validation.utils.RuleBasedValidStats import RuleBasedValidStats
from validation.core.RuleMap import RuleMap
from validation.core.Literal import Literal
import time

class RuleBasedValidation:
    def __init__(self, endpoint, node_order, shapesDict, logOutput,
                 validTargetsOutput, invalidTargetsOutput, statsOutput, tracesOutput):
        self.endpoint = endpoint
        self.node_order = node_order
        self.shapesDict = shapesDict

        self.targetShapes = self.extractTargetShapes()
        self.targetShapePredicates = [s.getId() for s in self.targetShapes]

        self.logOutput = logOutput
        self.validOutput = validTargetsOutput
        self.violatedOutput = invalidTargetsOutput
        self.statsOutput = statsOutput
        self.stats = RuleBasedValidStats()

        self.tracesOutput = tracesOutput
        self.startOfVerification = time.time() * 1000.0
        self.tracesOutput.write("Target, #TripleInThatClass, TimeSinceStartOfVerification(ms)\n")

        self.evaluatedShapes = []  # used for the filtering queries
        self.prevEvalShapeName = None

    def exec(self):
        firstShapeEval = self.shapesDict[self.node_order.pop(0)]
        depth = 0  # evaluation order
        self.logOutput.write("Retrieving (initial) targets ...")
        targets = self.extractTargetAtoms(firstShapeEval)
        self.logOutput.write("\nTargets retrieved.")
        self.logOutput.write("\nNumber of targets:\n" + str(len(targets)))
        self.stats.recordInitialTargets(str(len(targets)))
        start = time.time()*1000.0
        state = EvalState(targets)
        self.validate(
            depth,
            state,
            firstShapeEval
        )
        finish = time.time()*1000.0
        elapsed = round(finish - start)
        self.stats.recordTotalTime(elapsed)
        print("Total execution time: ", str(elapsed), " ms")
        self.logOutput.write("\nMaximal (initial) number or rules in memory: " + str(self.stats.maxRuleNumber))
        self.writeTargetsToFile(state)
        self.stats.writeAll(self.statsOutput)

        fileManagement.closeFile(self.validOutput)
        fileManagement.closeFile(self.violatedOutput)
        fileManagement.closeFile(self.statsOutput)
        fileManagement.closeFile(self.logOutput)
        fileManagement.closeFile(self.tracesOutput)

    def getInstancesList(self, prevEvalShapeName):
        '''
        Returns the valid and invalid instances of the previous evaluated shape (if there is one).
        :param prevEvalShapeName: string containing the name of the shape of interest
        :return:
        '''
        if prevEvalShapeName is None:
            return [], []

        return self.shapesDict[prevEvalShapeName].bindings, self.shapesDict[prevEvalShapeName].invalidBindings

    def filteringTargetQuery(self, shape, bType, valList, invList):
        '''
        Local variables:
            maxSplitNumber: heuristic of maximum possible number of instances considered for using filtering queries
                            instead of the initial target query (currently hard-coded to 256)
            maxInstancesPerQuery: number from which the list is going to start being split because of the max
                            number of characters allowed in a query
        '''
        self.logOutput.write("\n" + bType + " instances shape: " + shape.id + " - child's (" + self.prevEvalShapeName + ")")
        #self.logOutput.write(" instances: " + str(len(valList)) + " val " + str(len(invList)) + " inv")
        return [shape.getTargetQuery()]

    def validTargetAtoms(self, shape, bType, prevValList, prevInvList):
        '''

        :param shape: current shape being evaluated
        :param bType: string containing instances type (either "valid" or "invalid")
        :param prevValList:
        :param prevInvList:
        :return:
        '''
        if len(prevValList) == 0:
            # no query to be evaluated since no new possible target literals can be found
            if len(prevInvList) > 0:
                shape.hasValidInstances = False
            return []  # no target literals retrieved
        else:
            query = self.filteringTargetQuery(shape, bType, prevValList, prevInvList)
            # when the lists are not split, the variable 'query' returns an array with one single query

            targetLiterals = set()
            for q in query:
                bindings = self.evalTargetQuery(shape, q)
                targetLiterals.update([Literal(shape.getId(), b["x"]["value"], True) for b in bindings])
            return targetLiterals

    def invalidTargetAtoms(self, shape, bType, prevValList, prevInvList):
        '''

        :param shape: current shape being evaluated
        :param bType: string containing instances type (either "valid" or "invalid")
        :param prevValList:
        :param prevInvList:
        :return:
        '''
        if len(prevInvList) == 0:
            return []
        else:
            query = self.filteringTargetQuery(shape, bType, prevValList, prevInvList)

            invalidBindings = set()
            qn = 0
            for q in query:
                bindings = self.evalTargetQuery(shape, q)
                print("^^^^^ bindings:", len(bindings))
                if qn == 0:
                    # update empty set
                    invalidBindings.update([Literal(shape.getId(), b["x"]["value"], True) for b in bindings])
                    qn += 1
                else:
                    invalidBindings.intersection([Literal(shape.getId(), b["x"]["value"], True) for b in bindings])
            print("invalidating...", len(invalidBindings))
            return invalidBindings

    # Extracts target atom from first evaluated shape
    def extractTargetAtoms(self, shape):
        return self.targetAtomsNaive(shape, shape.getTargetQuery())

    def evalTargetQuery(self, shape, query):
        if query is None:
            return []  # when a network has only some targets, a shape without a target class returns no new bindings
        query += " ORDER BY ?x"
        self.logOutput.write("\nEvaluating query:\n" + query)
        startQ = time.time()*1000.0
        eval = self.endpoint.runQuery(
            shape.getId(),
            query,
            "JSON"
        )
        endQ = time.time()*1000.0
        self.logOutput.write("\nelapsed: " + str(endQ - startQ) + " ms\n")
        self.stats.recordQueryExecTime(endQ - startQ)
        self.stats.recordQuery()
        return eval["results"]["bindings"]

    def targetAtomsNaive(self, shape, targetQuery):
        '''

        :param shape:
        :param targetQuery: initial targetQuery is set in shape's definition file (json file)
        :return:
        '''
        bindings = self.evalTargetQuery(shape, targetQuery)
        return [Literal(shape.getId(), b["x"]["value"], True) for b in bindings]  # target literals

    def extractTargetShapes(self):
        return [s for name, s in self.shapesDict.items() if self.shapesDict[name].getTargetQuery() is not None]

    def checkPrevShapeValidationIsPending(self, prevEvalShapeName):
        if prevEvalShapeName is not None:
            prevShape = self.shapesDict[prevEvalShapeName]
            return len(prevShape.bindings) == 0 and len(prevShape.invalidBindings) == 0
        return False

    def validate(self, depth, state, focusShape):  # Algorithm 1 modified (SHACL2SPARQL)
        # termination condition 1: all targets are validated/violated  # does not apply anymore since we do not
        #if len(state.remainingTargets) == 0:                          # get all possible initial targets (considering
        #    return                                                    # all shapes of the network) from the beginning

        # termination condition 2: all shapes have been visited
        if len(state.visitedShapes) == len(self.shapesDict):
            for t in state.remainingTargets:
                self.registerTarget(t, True, depth, "not violated after termination", None, state)
            return

        self.logOutput.write("\n\n********************************")
        self.logOutput.write("\nStarting validation at depth: " + str(depth))

        self.evalShape(state, focusShape, depth)  # validate current selected shape

        # select next shape to be evaluated from the already defined list with the evaluation order
        if len(self.node_order) > 0:  # if there are more shapes to be evaluated
            self.nextEvalShape = self.shapesDict[self.node_order.pop(0)]
            self.evaluatedShapes.append(focusShape)
            if self.nextEvalShape.targetQuery is not None:
                self.logOutput.write("\n\n****************************************\n********************************")
                self.logOutput.write("\nRetrieving (next) targets ...")

                targets = self.extractTargetAtoms(self.nextEvalShape)
                state.remainingTargets.update(targets)
        else:
            self.nextEvalShape = None

        self.validate(depth + 1, state, self.nextEvalShape)

    def writeTargetsToFile(self, state):
        """
        Saves to local file the new validated target

        :param state:
        :return:
        """
        for valid in state.validTargets:
            self.validOutput.write(valid)

        for invalid in state.invalidTargets:
            self.violatedOutput.write(invalid)

        for trace in state.traces:
            self.tracesOutput.write(trace)

    def registerTarget(self, t, isValid, depth, logMessage, focusShape, state):
        fshape = ", focus shape " + focusShape.id if focusShape is not None else ""
        log = t.getStr() + ", depth " + str(depth) + fshape + ", " + logMessage + "\n"

        instance = "<" + t.getArg() + ">"
        #for key, value in getPrefixes().items():  # for using prefix notation in the instances of the query
        #    value = value[1:-1]
        #    if value in t.getArg():
        #        instance = instance.replace(value, key + ":")[1:-1]

        if isValid:
            self.shapesDict[t.getPredicate()].bindings.add(instance)
            state.validTargets.add(log)
        else:
            self.shapesDict[t.getPredicate()].invalidBindings.add(instance)
            state.invalidTargets.add(log)

        targetType = "valid" if isValid else "violated"
        traceLog = targetType + ", " + \
                    str(state.tracesCount) + ", " + \
                    str(round(time.time() * 1000.0 - self.startOfVerification)) + "\n"

        state.traces.add(traceLog)
        state.tracesCount += 1


    def saturate(self, state, depth, s):
        negated = self.negateUnMatchableHeads(state, depth, s)
        inferred = self.applyRules(state, depth, s)

        if negated or inferred:
            self.saturate(state, depth, s)

    # INFER procedure performs 2 types of inferences:
    # 1. If the set of rules contains a rule and each of the rule bodies has already been inferred
    #    => head of the rule is inferred, rule dropped.
    # 2. If the negation of any rule body has already been inferred
    #    => this rule cannot be applied (rule head not inferred) so the entire entire rule is dropped.
    def applyRules(self, state, depth, s):
        retainedRules = RuleMap()                                                              # (2)
        freshLiterals = set(filter(lambda rule: rule is not None,                              # (4)
                                   [self._applyRules(head, bodies, state, retainedRules)
                                    for head, bodies in state.ruleMap.map.items()])            # (3)
                            )
        state.ruleMap = retainedRules
        state.assignment.update(freshLiterals)

        if len(freshLiterals) == 0:
            return False

        candidateValidTargets = {a for a in freshLiterals if a.getPredicate() in self.targetShapePredicates}
        remaining = set()
        for t in state.remainingTargets:
            if t in candidateValidTargets:
                if t.getIsPos():
                    #state.validTargets.add(t)
                    self.registerTarget(t, True, depth, "", s, state)
                else:
                    #state.invalidTargets.add(t)
                    self.registerTarget(t, False, depth, "", s, state)
            else:
                remaining.add(t)

        state.remainingTargets = remaining

        self.logOutput.write("\nRemaining targets: " + str(len(state.remainingTargets)))
        return True

    def _applyRules(self, head, bodies, state, retainedRules):
        for body in bodies:
            if body.issubset(state.assignment):  # means that there is at least one invalid rule
                return head

            matches = [a.getNegation() for a in body if a.getNegation() in state.assignment]  # ***
            if len(matches) == 0:  # no match
                retainedRules.addRule(head, body)  # not invalid
            return None

    # validateFocusShape
    def evalShape(self, state, s, depth):
        '''
        Saturate only if the current shape is connected in the network as a parent to a shape that was already
        evaluated and has any valid instances. This is,

        if the child node (previously evaluated shape) contains only invalid instances, all retrieved instances of the
        shape being currently evaluated were registered as invalid so there is no need to validate min/max constraints.

        :param state:
        :param s: focus shape
        :param depth:
        '''
        self.logOutput.write("\nEvaluating queries for shape " + s.getId())

        if s.hasValidInstances:
            self.evalConstraints(state, s)  # 'eval Disjunct'
            state.evaluatedPredicates.update(s.getPredicates())
            #self.saveRuleNumber(state)
            self.logOutput.write("\nStarting saturation ...")
            startS = time.time()*1000.0
            self.saturate(state, depth, s)
            endS = time.time()*1000.0
            self.stats.recordSaturationTime(endS - startS)
            self.logOutput.write("\nsaturation ...\nelapsed: " + str(endS - startS) + " ms")
        else:
            self.logOutput.write("\nNo saturation for shape ..." + s.getId())

        state.addVisitedShape(s)

        self.logOutput.write("\n\nValid targets: " + str(len(state.validTargets)))
        self.logOutput.write("\nInvalid targets: " + str(len(state.invalidTargets)))
        self.logOutput.write("\nRemaining targets: " + str(len(state.remainingTargets)))

    def saveRuleNumber(self, state):
        ruleNumber = state.ruleMap.getRuleNumber()
        self.logOutput.write("\nNumber of rules: " + str(ruleNumber))
        self.stats.recordNumberOfRules(ruleNumber)

    def filteringConstraintQuery(self, shape, templateQuery, prevValidInstances, prevInvalidInstances,
                         maxSplitNumber, maxInstancesPerQuery, qType):
        if self.prevEvalShapeName is not None \
                and len(prevValidInstances) > 0 and len(prevInvalidInstances) > 0 \
                and len(prevValidInstances) <= maxSplitNumber:
            VALUES_clauses = ""
            refPaths = "\n" if qType == "max" else ''
            formattedInstancesSplit = self.getFormattedInstances(prevValidInstances, "", maxInstancesPerQuery)
            for c in shape.constraints:
                if c.shapeRef == self.prevEvalShapeName:
                    var = " ?" + c.variables[0]
                    VALUES_clauses += "VALUES" + var + " {$instances$}\n"
                    if qType == "max":
                        focusVar = c.varGenerator.getFocusNodeVar()
                        refPaths += "?" + focusVar + " " + c.path + var + ".\n"

            return [templateQuery.replace("$to_be_replaced$",
                                           VALUES_clauses.replace("$instances$", sublist) + refPaths)
                    for sublist in formattedInstancesSplit]
        else:
            return [templateQuery.replace("$to_be_replaced$", "\n")]

    def evalConstraints(self, state, s):
        prevValList, prevInvList = self.getInstancesList(self.prevEvalShapeName)

        maxSplitNumber = s.maxSplitSize
        maxInstancesPerQuery = 80

        minQuery = self.filteringConstraintQuery(s, s.minQuery.getSparql(), prevValList, prevInvList,
                                             maxSplitNumber, maxInstancesPerQuery, "min")
        for queryStr in minQuery:
            self.evalQuery(state, s.minQuery, queryStr, s)

        for q in s.maxQueries:
            maxQuery = self.filteringConstraintQuery(s, q.getSparql(), prevValList, prevInvList,
                                                 maxSplitNumber, maxInstancesPerQuery, "max")
            for queryStr in maxQuery:
                self.evalQuery(state, q, queryStr, s)

    def evalQuery(self, state, q, query, s):
        self.logOutput.write("\n\nEvaluating query:\n" + query)
        startQ = time.time()*1000.0
        eval = self.endpoint.runQuery(q.getId(), query, "JSON")
        endQ = time.time()*1000.0
        self.logOutput.write("\nelapsed: " + str(endQ - startQ) + " ms\n")
        self.stats.recordQueryExecTime(endQ - startQ)

        bindings = eval["results"]["bindings"]  # list of obtained 'bindingsSet' from the endpoint

        self.logOutput.write("\nNumber of solution mappings: " + str(len(bindings)) + "\n")
        self.stats.recordNumberOfSolutionMappings(len(bindings))
        self.stats.recordQuery()
        queryRP = q.getRulePattern()
        qH = queryRP.getHead()
        qB = queryRP.getBody()
        qV = queryRP.getVariables()
        shapeRP = s.getRulePatterns()[0]
        sH = shapeRP.getHead()
        sB = shapeRP.getBody()
        sV = shapeRP.getVariables()
        bvars = set(bindings[0].keys()) if len(bindings) > 0 else set()

        startG = time.time() * 1000.0

        #for b in bindings:
            #self.evalBindingSet(state, b, queryRP.getVariables(), queryRP.getHead(), queryRP.getBody(), queryRP,
            #                    shapeRP.getVariables(), shapeRP.getHead(), shapeRP.getBody(), shapeRP)

        qRules = [state.ruleMap.addRule(
            Literal(
                qH.getPredicate(),
                binding[qH.getArg()]["value"],
                qH.getIsPos()),
            frozenset({Literal(a.getPredicate(),
                               binding[a.getArg()]["value"],
                               a.getIsPos())
                       for a in qB})
        ) for binding in bindings if bvars.issuperset(qV)]

        sRules = [state.ruleMap.addRule(
            Literal(
                sH.getPredicate(),
                binding[sH.getArg()]["value"],
                sH.getIsPos()),
            frozenset({Literal(a.getPredicate(),
                               binding[a.getArg()]["value"],
                               a.getIsPos())
                       for a in sB})
        ) for binding in bindings if bvars.issuperset(sV)]

        endG = time.time() * 1000.0

        self.stats.recordGroundingTime(endG - startG)
        self.logOutput.write("\nGrounding rules ... \nelapsed: " + str(endG - startG) + " ms\n")

    '''def evalBindingSet(self, state, bs, qV, qH, qB, qRP, sV, sH, sB, sRP):
        bindingVars = set(bs.keys())
        self._evalBindingSet(state, bs, bindingVars, qV, qH, qB, qRP)
        #for p in shapeRPs:  # for each pattern in the set of rule patterns (but a shape contains only one pattern
        self._evalBindingSet(state, bs, bindingVars, sV, sH, sB, sRP)

    def _evalBindingSet(self, state, bs, bindingVars, vars, head, body, rp):
        if bindingVars.issuperset(vars):
            state.ruleMap.addRule(
                rp.instantiateAtom(head, bs),
                frozenset({rp.instantiateAtom(a, bs) for a in body})
            )'''

    def negateUnMatchableHeads(self, state, depth, s):
        '''
        This procedure derives negative information
        For any (possibly negated) atom 'a' that is either a target or appears in some rule, we
        may be able to infer that 'a' cannot hold:
          if 'a' is not in state.assignment
          if the query has already been evaluated,
          and if there is not rule with 'a' as its head.
        Thus, in such case, 'not a' is added to state.assignment.

        :param state:
        :param depth:
        :param s:
        :return:
        '''
        ruleHeads = state.ruleMap.keySet()

        initialAssignmentSize = len(state.assignment)

        # first negate unmatchable body atoms (add not satisfied body atoms)
        allBodyAtoms = state.ruleMap.getAllBodyAtoms()
        state.assignment.update({a.getNegation() if a.getIsPos() else a
                                 for a in allBodyAtoms
                                 if not ((a.getPredicate() not in state.evaluatedPredicates)
                                          or (a.getAtom() in ruleHeads)
                                          or (a in state.assignment))}
                                )

        # then negate unmatchable targets
        remaining = set()
        for a in state.remainingTargets:
            if self.isSatisfiable(a, state, ruleHeads):
                remaining.add(a)
            else:
                #state.invalidTargets.add(a)
                state.assignment.add(a.getNegation())
                self.registerTarget(a, False, depth, "", s, state)

        state.remainingTargets = remaining

        return initialAssignmentSize != len(state.assignment)  # False when no new assignments are found

    #def getNegatedAtom(self, a):
    #    return a.getNegation() if a.getIsPos() else a

    def isSatisfiable(self, a, state, ruleHeads):
        return (a.getPredicate() not in state.evaluatedPredicates) \
                or (a.getAtom() in ruleHeads) \
                or (a in state.assignment)

class EvalState:
    def __init__(self, targetLiterals):
        self.remainingTargets = targetLiterals
        self.ruleMap = RuleMap()
        self.assignment = set()
        self.visitedShapes = set()
        self.evaluatedPredicates = set()
        self.validTargets = set()
        self.invalidTargets = set()
        self.traces = set()
        self.tracesCount = 0

    def addVisitedShape(self, s):
        self.visitedShapes.add(s)
