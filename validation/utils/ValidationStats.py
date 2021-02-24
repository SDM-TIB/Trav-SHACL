# -*- coding: utf-8 -*-
__author__ = "Monica Figuera"


class ValidationStats:
    def __init__(self):
        self.targets = 0
        self.valid = 0
        self.invalid = 0

        self.total_sol_mappings = 0
        self.max_sol_mappings = 0

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
        output_file.write("all targets:\n" + str(self.targets))
        output_file.write("\nvalid targets:\n" + str(self.valid))
        output_file.write("\ninvalid targets:\n" + str(self.invalid))
        output_file.write("\nmax number of rules in memory (2x max number of mappings for a query):\n" + str(self.max_sol_mappings*2))
        output_file.write("\ntotal number of rules (2x total number of mappings):\n" + str(self.total_sol_mappings*2))
        output_file.write("\nnumber of queries:\n" + str(self.number_of_queries))
        output_file.write("\nmax exec time for a query:\n" + str(self.max_query_exec_time))
        output_file.write("\ntotal query exec time:\n" + str(self.total_query_exec_time))
        output_file.write("\nmax interleaving (+ query exec) time for a query:\n" + str(self.max_interleaving_time))
        output_file.write("\ntotal interleaving (+ query exec) time:\n" + str(self.total_interleaving_time))
        output_file.write("\nmax (deferred) saturation time:\n" + str(self.max_saturation_time))
        output_file.write("\ntotal (deferred) saturation time:\n" + str(self.total_saturation_time))
        output_file.write("\ntotal time:\n" + str(self.totalTime) + "\n")

    def record_number_of_targets(self, valid_count, invalid_count):
        self.valid = valid_count
        self.invalid = invalid_count
        self.targets = valid_count + invalid_count

    def record_interleaving_time(self, ms):
        if ms > self.max_interleaving_time:
            self.max_interleaving_time = ms

        self.total_interleaving_time += ms

    def record_query_exec_time(self, ms):
        if ms > self.max_query_exec_time:
            self.max_query_exec_time = ms

        self.total_query_exec_time += ms

    def record_query(self):
        self.number_of_queries += 1

    def record_number_of_sol_mappings(self, k):
        if k > self.max_sol_mappings:
            self.max_sol_mappings = k

        self.total_sol_mappings += k

    def record_saturation_time(self, ms):
        if ms > self.max_saturation_time:
            self.max_saturation_time = ms

        self.total_saturation_time += ms

    def record_total_time(self, ms):
        self.totalTime = ms

    def update_log(self, log):
        self.validation_log += log

    def write_validation_log(self, validation_log_output):
        validation_log_output.write(self.validation_log)
