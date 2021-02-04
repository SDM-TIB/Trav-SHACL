# -*- coding: utf-8 -*-
__author__ = "Monica Figuera"


class ValidationStats:
    def __init__(self):
        self.targets = 0
        self.maxRuleNumber = 0
        self.totalRuleNumber = 0
        self.totalSolutionMappings = 0
        self.maxSolutionMappings = 0

        self.totalQueryExectime = 0
        self.maxQueryExectime = 0
        self.totalInterleavingTime = 0
        self.maxInterleavingTime = 0
        self.totalSaturationTime = 0
        self.maxSaturationTime = 0
        self.numberOfQueries = 0
        self.totalTime = 0

        self.validation_log = ''

    def writeAll(self, statsOutput):
        statsOutput.write("targets:\n" + str(self.targets))
        statsOutput.write("\nmax number of rules in memory (2x max number of mappings for a query):\n" + str(self.maxSolutionMappings*2))
        statsOutput.write("\ntotal number of rules in memory (2x total number of mappings):\n" + str(self.totalSolutionMappings*2))
        statsOutput.write("\nnumber of queries:\n" + str(self.numberOfQueries))
        statsOutput.write("\nmax exec time for a query:\n" + str(self.maxQueryExectime))
        statsOutput.write("\ntotal query exec time:\n" + str(self.totalQueryExectime))
        statsOutput.write("\nmax interleaving time for a query:\n" + str(self.maxInterleavingTime))
        statsOutput.write("\ntotal interleaving time:\n" + str(self.totalInterleavingTime))
        statsOutput.write("\nmax saturation time:\n" + str(self.maxSaturationTime))
        statsOutput.write("\ntotal saturation time:\n" + str(self.totalSaturationTime))
        statsOutput.write("\ntotal time:\n" + str(self.totalTime) + "\n")

    def writeValidationLog(self, validationLogOutput):
        validationLogOutput.write(self.validation_log)

    def recordTargets(self, k):
        self.targets = k

    def recordInterleavingTime(self, ms):
        if ms > self.maxInterleavingTime:
            self.maxInterleavingTime = ms

        self.totalInterleavingTime += ms

    def recordQueryExecTime(self, ms):
        if ms > self.maxQueryExectime:
            self.maxQueryExectime = ms

        self.totalQueryExectime += ms

    def recordSaturationTime(self, ms):
        if ms > self.maxSaturationTime:
            self.maxSaturationTime = ms

        self.totalSaturationTime += ms

    def recordNumberOfSolutionMappings(self, k):
        if k > self.maxSolutionMappings:
            self.maxSolutionMappings = k

        self.totalSolutionMappings += k

    def recordTotalTime(self, ms):
        self.totalTime = ms

    def recordQuery(self):
        self.numberOfQueries += 1

    def updateValidationLog(self, log):
        self.validation_log = ''.join([self.validation_log, log])
