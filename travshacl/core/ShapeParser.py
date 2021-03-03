# -*- coding: utf-8 -*-
__author__ = "Monica Figuera and Philipp D. Rohde"

import json
import os
from urllib.parse import urlparse

from travshacl.core.Shape import Shape
from travshacl.utils.VariableGenerator import VariableGenerator
from travshacl.constraints.MaxOnlyConstraint import MaxOnlyConstraint
from travshacl.constraints.MinMaxConstraint import MinMaxConstraint
from travshacl.constraints.MinOnlyConstraint import MinOnlyConstraint


class ShapeParser:
    """Used for parsing shape definitions from files to the internal representation."""

    def __init__(self):
        pass

    def parse_shapes_from_dir(self, path, shape_format, use_selective_queries, max_split_size, order_by_in_queries):
        """
        Parses all files of a certain file extension in the directory.
        It assumes that each file represents one SHACL shape.

        :param path: the path to the directory that stores the shapes files
        :param shape_format: the representation format of the shape definitions
        :param use_selective_queries: indicates whether or not selective queries are used
        :param max_split_size: maximum number of instances per query
        :param order_by_in_queries: indicates whether or not to use the ORDER BY clause
        :return: list of Shapes parsed from the files
        """
        file_extension = self.get_file_extension(shape_format)
        files_abs_paths = []

        # r=root, d=directories, f=files
        for r, d, f in os.walk(path):
            for file in f:
                if file_extension in file:
                    files_abs_paths.append(os.path.join(r, file))

        if not files_abs_paths:
            raise FileNotFoundError(path + " does not contain any shapes of the format " + shape_format)

        if shape_format == "JSON":
            return [self.parse_json(
                path=p,
                use_selective_queries=use_selective_queries,
                max_split_size=max_split_size,
                order_by_in_queries=order_by_in_queries
            ) for p in files_abs_paths]
        else:  # TODO: implement parsing of TTL format
            print("Unexpected format: " + shape_format)

    @staticmethod
    def get_file_extension(shape_format):
        if shape_format == "SHACL":
            return ".ttl"
        else:
            return ".json"  # dot added for convenience

    def parse_json(self, path, use_selective_queries, max_split_size, order_by_in_queries):
        """
        Parses a particular file and converts its content into the internal representation of a SHACL shape.

        :param path: the path to the shapes file
        :param use_selective_queries: indicates whether or not selective queries are used
        :param max_split_size: maximum number of instances per query
        :param order_by_in_queries: indicates whether or not to use the ORDER BY clause
        :return: Shape object representing the parsed SHACL shape
        """
        target_query = None
        target_type = None

        file = open(path, "r")
        obj = json.load(file)
        target_def = obj.get("targetDef")
        name = obj["name"]
        id_ = name + "_d1"  # str(i + 1) but there is only one set of conjunctions
        constraints = self.parse_constraints(obj["constraintDef"]["conjunctions"], target_def, id_)

        include_sparql_prefixes = self.abbreviated_syntax_used(constraints)
        referenced_shapes = self.shape_references(obj["constraintDef"]["conjunctions"][0])

        if target_def is not None:
            target_query = target_def["query"]

            target_def_copy = target_def.copy()
            del target_def_copy["query"]
            target_type = list(target_def_copy.keys())[0]

            if urlparse(target_def[target_type]).netloc != '':  # if the target node is a url, add '<>' to it
                target_def = '<' + target_def[target_type] + '>'
            else:
                target_def = target_def[target_type]

        return Shape(name, target_def, target_type, target_query, constraints, id_, referenced_shapes,
                     use_selective_queries, max_split_size, order_by_in_queries, include_sparql_prefixes)

    @staticmethod
    def abbreviated_syntax_used(constraints):
        """
        Run after parsingConstraints.
        Returns false if the constraints' predicates are using absolute paths instead of abbreviated ones
        :param constraints: all shape constraints
        :return: True if prefix notation is used, False otherwise
        """
        for c in constraints:
            if c.path.startswith("<") and c.path.endswith(">"):
                return False
        return True

    @staticmethod
    def shape_references(constraints):
        """
        Gets the shapes referenced by the given constraints.

        :param constraints: the constraints to get the referenced shapes for
        :return: Python dictionary with the referenced shapes and the path referencing the shape
        """
        return {c.get("shape"): c.get("path") for c in constraints if c.get("shape") is not None}

    def parse_constraints(self, array, target_def, constraints_id):
        """
        Parses all constraints of a shape.

        :param array: list of constraints belonging to the shape
        :param target_def: the target definition of the shape
        :param constraints_id: suffix for the constraint IDs
        :return: list of constraints in internal constraint representation
        """
        var_generator = VariableGenerator()
        return [self.parse_constraint(var_generator, array[0][i], constraints_id + "_c" + str(i + 1), target_def)
                for i in range(len(array[0]))]

    @staticmethod
    def parse_constraint(var_generator, obj, id_, target_def):
        """
        Parses one constraint to the internal representation.

        :param var_generator: reference to the VariableGenerator instance to use for variable generation for SPARQL queries
        :param obj: the constraint in its original representation
        :param id_: suffix for the constraint ID
        :param target_def: the target definition of the associated shape
        :return: constraint in internal representation
        """
        min_ = obj.get("min")
        max_ = obj.get("max")
        shape_ref = obj.get("shape")
        datatype = obj.get("datatype")
        value = obj.get("value")
        path = obj.get("path")
        negated = obj.get("negated")

        o_min = None if (min_ is None) else int(min_)
        o_max = None if (max_ is None) else int(max_)
        o_shape_ref = None if (shape_ref is None) else str(shape_ref)
        o_datatype = None if (datatype is None) else str(datatype)
        o_value = None if (value is None) else str(value)
        o_path = None if (path is None) else str(path)
        o_neg = True if (negated is None) else not negated  # True means it is a positive constraint

        if urlparse(path).netloc != '':  # if the predicate is a url, add '<>' to it
            o_path = '<' + path + '>'

        if o_path is not None:
            if o_min is not None:
                if o_max is not None:
                    return MinMaxConstraint(var_generator, id_, o_path, o_min, o_max, o_neg, o_datatype, o_value, o_shape_ref, target_def)
                return MinOnlyConstraint(var_generator, id_, o_path, o_min, o_neg, o_datatype, o_value, o_shape_ref, target_def)
            if o_max is not None:
                return MaxOnlyConstraint(var_generator, id_, o_path, o_max, o_neg, o_datatype, o_value, o_shape_ref, target_def)
