package unibz.shapes.valid.rule;

import unibz.shapes.util.Output;

public class RuleBasedValidStats {

        void writeAll(Output statsOutput) {
            statsOutput.write("targets:\n" + initialTargets);
            statsOutput.write("max number of solution mappings for a query:\n" + maxSolutionMappings);
            statsOutput.write("total number of solution mappings:\n" + totalSolutionMappings);
            statsOutput.write("max number of rules in memory:\n" + maxRuleNumber);
            statsOutput.write("number of queries:\n" + numberOfQueries);
            statsOutput.write("max exec time for a query:\n" + maxQueryExectime);
            statsOutput.write("total query exec time:\n" + totalQueryExectime);
            statsOutput.write("max grounding time for a query:\n" + maxGroundingTime);
            statsOutput.write("total grounding time:\n" + totalGroundingTime);
            statsOutput.write("max saturation time:\n" + maxSaturationTime);
            statsOutput.write("total saturation time:\n" + totalSaturationTime);
            statsOutput.write("total time:\n" + totalTime);
        }

        private int initialTargets = 0;

        int maxRuleNumber = 0;
        private int totalSolutionMappings = 0;
        private int maxSolutionMappings = 0;

        private long totalQueryExectime = 0;
        private long maxQueryExectime = 0;
        private long totalGroundingTime = 0;
        private long maxGroundingTime = 0;
        private long totalSaturationTime = 0;
        private long maxSaturationTime = 0;
        private int numberOfQueries = 0;

        private long totalTime = 0;

        void recordInitialTargets(int k) {
            initialTargets = k;
        }

        void recordGroundingTime(long ms) {
            if (ms > maxGroundingTime) {
                maxGroundingTime = ms;
            }
            totalGroundingTime += ms;
        }

        void recordQueryExecTime(long ms) {
            if (ms > maxQueryExectime) {
                maxQueryExectime = ms;
            }
            totalQueryExectime += ms;

        }

        void recordSaturationTime(long ms) {
            if (ms > maxSaturationTime) {
                maxSaturationTime = ms;
            }
            totalSaturationTime += ms;
        }

        void recordNumberOfRules(int k) {
            if (k > maxRuleNumber) {
                maxRuleNumber = k;
            }
        }

        void recordNumberOfSolutionMappings(int k) {
            if (k > maxSolutionMappings) {
                maxSolutionMappings = k;
            }
            totalSolutionMappings += k;
        }

//        void recordDecidedTargets(int numberOfargets) {
//
//        }

        void recordTotalTime(long ms) {
            totalTime = ms;
        }

        void recordQuery() {
            numberOfQueries++;
        }
}
