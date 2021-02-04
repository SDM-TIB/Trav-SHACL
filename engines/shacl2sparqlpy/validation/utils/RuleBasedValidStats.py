# -*- coding: utf-8 -*-

class RuleBasedValidStats:
    def __init__(self):
        self.initialTargets = 0

        self.maxRuleNumber = 0
        self.totalSolutionMappings = 0
        self.maxSolutionMappings = 0

        self.totalQueryExectime = 0
        self.maxQueryExectime = 0
        self.totalGroundingTime = 0
        self.maxGroundingTime = 0
        self.totalSaturationTime = 0
        self.maxSaturationTime = 0
        self.numberOfQueries = 0

        self.totalTime = 0

    def writeAll(self, statsOutput):
        statsOutput.write("(initial) targets:\n" + str(self.initialTargets))
        statsOutput.write("\nmax number of solution mappings for a query:\n" + str(self.maxSolutionMappings))
        statsOutput.write("\ntotal number of solution mappings:\n" + str(self.totalSolutionMappings))
        statsOutput.write("\nmax number of rules in memory:\n" + str(self.maxRuleNumber))
        statsOutput.write("\nnumber of queries:\n" + str(self.numberOfQueries))
        statsOutput.write("\nmax exec time for a query:\n" + str(self.maxQueryExectime))
        statsOutput.write("\ntotal query exec time:\n" + str(self.totalQueryExectime))
        statsOutput.write("\nmax grounding time for a query:\n" + str(self.maxGroundingTime))
        statsOutput.write("\ntotal grounding time:\n" + str(self.totalGroundingTime))
        statsOutput.write("\nmax saturation time:\n" + str(self.maxSaturationTime))
        statsOutput.write("\ntotal saturation time:\n" + str(self.totalSaturationTime))
        statsOutput.write("\ntotal time:\n" + str(self.totalTime) + "\n")

    def recordInitialTargets(self, k):
        self.initialTargets = k

    def recordGroundingTime(self, ms):
        if ms > self.maxGroundingTime:
            self.maxGroundingTime = ms

        self.totalGroundingTime += ms

    def recordQueryExecTime(self, ms):
        if ms > self.maxQueryExectime:
            self.maxQueryExectime = ms

        self.totalQueryExectime += ms

    def recordSaturationTime(self, ms):
        if ms > self.maxSaturationTime:
            self.maxSaturationTime = ms

        self.totalSaturationTime += ms

    def recordNumberOfRules(self, k):
        if k > self.maxRuleNumber:
            self.maxRuleNumber = k

    def recordNumberOfSolutionMappings(self, k):
        if k > self.maxSolutionMappings:
            self.maxSolutionMappings = k

        self.totalSolutionMappings += k

    def recordTotalTime(self, ms):
        self.totalTime = ms

    def recordQuery(self):
        self.numberOfQueries += 1
