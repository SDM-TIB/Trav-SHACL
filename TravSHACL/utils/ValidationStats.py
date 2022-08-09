# -*- coding: utf-8 -*-
__author__ = 'Monica Figuera'


class ValidationStats:
    """Statistics collected during the validation process."""

    def __init__(self):
        self.targets = 0
        self.valid = 0
        self.invalid = 0

        self.total_sol_mappings = 0
        self.max_sol_mappings = 0
        self.total_rules = 0
        self.max_rules = 0

        self.max_query_exec_time = 0
        self.total_query_exec_time = 0
        self.max_interleaving_time = 0
        self.total_interleaving_time = 0
        self.max_saturation_time = 0
        self.total_saturation_time = 0
        self.number_of_queries = 0
        self.totalTime = 0

        self.validation_log = ''

    def write_all_stats(self, output_file):
        """
        Writes all collected statistics to the output file.

        :param output_file: the file to be used for writing the statistics
        """
        output_file.write('all targets:\n' + str(self.targets))
        output_file.write('\nvalid targets:\n' + str(self.valid))
        output_file.write('\ninvalid targets:\n' + str(self.invalid))
        output_file.write('\nmax number of solution mappings for a query:\n' + str(self.max_sol_mappings))
        output_file.write('\ntotal number of solution mappings:\n' + str(self.total_sol_mappings))
        output_file.write('\nmax number of rules in memory:\n' + str(self.max_rules))
        output_file.write('\ntotal number of rules:\n' + str(self.total_rules))
        output_file.write('\nnumber of queries:\n' + str(self.number_of_queries))
        output_file.write('\nmax exec time for a query:\n' + str(self.max_query_exec_time))
        output_file.write('\ntotal query exec time:\n' + str(self.total_query_exec_time))
        output_file.write('\nmax interleaving (+ query exec) time for a query:\n' + str(self.max_interleaving_time))
        output_file.write('\ntotal interleaving (+ query exec) time:\n' + str(self.total_interleaving_time))
        output_file.write('\nmax (deferred) saturation time:\n' + str(self.max_saturation_time))
        output_file.write('\ntotal (deferred) saturation time:\n' + str(self.total_saturation_time))
        output_file.write('\ntotal time:\n' + str(self.totalTime) + '\n')

    def record_number_of_targets(self, valid_count, invalid_count):
        """
        Records the total number of targets for the validation.

        :param valid_count: number of valid targets
        :param invalid_count: number of invalid targets
        """
        self.valid = valid_count
        self.invalid = invalid_count
        self.targets = valid_count + invalid_count

    def record_interleaving_time(self, ms):
        """
        Records the time (in milliseconds) necessary for the interleaving process.

        :param ms: time in milliseconds passed for the interleaving step to be recorded
        """
        if ms > self.max_interleaving_time:
            self.max_interleaving_time = ms

        self.total_interleaving_time += ms

    def record_query_exec_time(self, ms):
        """
        Records the time (in milliseconds) necessary for query execution.

        :param ms: time in milliseconds passed for the query execution to be recorded
        """
        if ms > self.max_query_exec_time:
            self.max_query_exec_time = ms

        self.total_query_exec_time += ms

    def record_query(self):
        """Increases the counter for keeping track of the number of queries executed."""
        self.number_of_queries += 1

    def record_number_of_sol_mappings(self, k):
        """
        Records the number of solution mappings for the queries executed.

        :param k: the number of mappings returned by an executed query
        """
        if k > self.max_sol_mappings:
            self.max_sol_mappings = k

        self.total_sol_mappings += k

    def record_current_number_of_rules(self, k):
        """
        Records the max number of rules in memory after executing a query.

        :param k: current number of rules in memory
        """
        if k > self.max_rules:
            self.max_rules = k

    def record_total_rules(self, k):
        """
        Records the total number of rules of the validation.

        :param k: total number of grounded rules
        """
        self.total_rules = k

    def record_saturation_time(self, ms):
        """
        Records the time (in milliseconds) necessary for saturation.

        :param ms: time in milliseconds passed for the saturation step to be recorded
        """
        if ms > self.max_saturation_time:
            self.max_saturation_time = ms

        self.total_saturation_time += ms

    def record_total_time(self, ms):
        """
        Records the overall execution time (in milliseconds) of the validation.

        :param ms: time in milliseconds passed for the total validation
        """
        self.totalTime = ms

    def update_log(self, log):
        """
        Updates the validation log.

        :param log: the new log entry to be added
        """
        self.validation_log += log

    def write_validation_log(self, validation_log_output):
        """
        Writes the validation log to file.

        :param validation_log_output: file handler for the validation log
        """
        validation_log_output.write(self.validation_log)
