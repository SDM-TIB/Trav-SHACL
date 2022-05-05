# -*- coding: utf-8 -*-
__author__ = "Monica Figuera and Philipp D. Rohde"

import json
import os
from urllib.parse import urlparse

import collections
from rdflib import BNode
from rdflib import Graph
from itertools import islice

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
            return [self.parse_ttl(
                filename=p,
                use_selective_queries=use_selective_queries,
                max_split_size=max_split_size,
                order_by_in_queries=order_by_in_queries
            ) for p in files_abs_paths]
            # print("Unexpected format: " + shape_format)

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
        prefixes = None
        if "prefix" in obj.keys():
            prefixes = obj["prefix"]
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
                     use_selective_queries, max_split_size, order_by_in_queries, include_sparql_prefixes, prefixes)

    def parse_ttl(self, filename, use_selective_queries, max_split_size, order_by_in_queries):
        """
        Parses a particular file and converts its content into the internal representation of a SHACL shape.

        :param filename: the path to the shapes file
        :param use_selective_queries: indicates whether selective queries are used
        :param max_split_size: maximum number of instances per query
        :param order_by_in_queries: indicates whether to use the ORDER BY clause
        :return: Shape object representing the parsed SHACL shape
        """

        g_file = Graph()  # create graph instance
        g_file.parse(filename)

        name = self.get_sname(g_file)
        id_ = name[0][0] + "_d1"  # str(i + 1) but there is only one set of conjunctions
        target_ref = name[0][1]  # object of te shape name

        # to get the target_ref and target_type
        data_type, data_query = self.get_targetdef(g_file)
        if data_type[0] is not None:
            target_def = data_type[0]
            target_query = data_query
            target_type = 'class'

        elif data_type[1] is not None:
            target_def = data_type[1]
            target_query = data_query
            target_type = 'node'

        else:
            target_def = None
            target_query = None
            target_type = None

        if target_def is not None:
            if urlparse(target_def).netloc != '':  # if the target node is a url, add '<>' to it
                target_def = '<' + target_def + '>'

        cons_dict = self.parse_all_const(g_file, name=name[0][0], target_def=target_def, target_type=target_type)

        const_array = list(cons_dict.values())  # change the format to an array
        constraints = self.parse_constraints_ttl(const_array, target_def, id_)

        include_sparql_prefixes = self.abbreviated_syntax_used(constraints)
        prefixes = None
        referenced_shapes = self.shape_references(const_array)

        # helps to navigate the shape.__compute_target_queries function
        referenced_shape = {'<' + key + '>': '<' + referenced_shapes[key] + '>'
                            for key in referenced_shapes.keys()
                            if urlparse(referenced_shapes[key]).netloc != ''}

        # to helps to navigate the ShapeSchema.compute_edges function
        if urlparse(name[0][0]).netloc != '':
            name_ = '<' + name[0][0] + '>'
        else:
            name_ = name[0][0]

        return Shape(name_, target_def, target_type, target_query, constraints, id_, referenced_shape,
                     use_selective_queries, max_split_size, order_by_in_queries, include_sparql_prefixes, prefixes)

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

    @staticmethod
    def chunks(datei, SIZE):
        """
        Break down list of input (dictionaries) into individual dictionaries

        :param SIZE: tells the length or size for each output
        :datei: list of input to be broken down
        :return: inputs divided in len(SIZE)
        """
        it = iter(datei)
        for i in range(0, len(datei), SIZE):
            yield {k: datei[k] for k in islice(it, SIZE)}

    @staticmethod
    def get_sname(filename):
        """
        extract the subject of the main shape

        :param filename: file to be parsed
        :return: the main shape
        """
        query = '''
                SELECT ?sub ?obj WHERE { 
                ?sub a ?obj. }
            '''

        return [[str(row.asdict()['sub'].toPython()), str(row.asdict()['obj'].toPython())]
                for row in filename.query(query)]

    @staticmethod
    def get_targetdef(filename):
        """
        extract the subject of the main shape

        :param filename: file to be parsed
        :return: the target node or  target class
        """

        type_list = ['targetClass', 'targetNode']
        datatype = []
        data_query = None
        select_stat = 'SELECT ?target WHERE { '
        select_end = 'SELECT ?x WHERE { ?x a <'
        top_q = '?name sh:'
        close = ' ?target. }'

        for i in type_list:
            query_sd = select_stat + top_q + i + close
            #query_ed = select_end + top_q + i
            target_def = filename.query(query_sd)
            if len(target_def) != 0:
                for row in target_def:
                    d_type = str(row.asdict()['target'].toPython())
                    datatype.append(d_type)
                    data_query = select_end + d_type + '> }'
            else:
                datatype.append(None)

        return datatype, data_query

    @staticmethod
    def get_query():
        query_1 = '''
        SELECT ?x_data ?y_data ?z_data
        WHERE { ?name sh:path ?x_data;
            ?y_data ?z_data.}
        '''

        query_2 = '''
        SELECT ?x_data ?y_data ?z1_data ?z2_data 
        WHERE { ?name sh:path ?x_data;
            ?y_data [?z1_data ?z2_data].}
        '''

        return query_1, query_2

    def get_res(self, filename):
        """

        :param filename: shape file in ttl format
        :return: valid response from query execution
        """

        query_1, query_2 = self.get_query()
        full_list_1 = []

        query_res_1 = filename.query(query_1)
        query_res_2 = filename.query(query_2)

        # to remove BNode
        BNode_list = []
        for row in query_res_2:
            BNode_list.append(row)

        for row in query_res_1:
            row = list(row)
            if type(row[2]) is BNode:
                row[2] = [BNode_list[0][2], BNode_list[0][3]]
                BNode_list.pop(0)
            full_list_1.append(row)

        return full_list_1

    def to_dict(self, filename):
        """

        :param filename: shape file in ttl format
        :return: convert the response list to dictionary
        """
        full_list = self.get_res(filename)
        full_dict_2 = collections.defaultdict(list)
        i = 0
        for row_data in full_list:
            # row = list(row)

            if str(row_data[1].split('#')[-1]) == 'path':
                i = i + 1
                row_data[0] = str(row_data[0]) + '_' + str(i)
                row_data[2] = str(row_data[2]) + '_' + str(i)
            else:
                row_data[0] = str(row_data[0]) + '_' + str(i)
                if type(row_data[2]) is not list:
                    row_data[2] = str(row_data[2]) + '_' + str(i)

            full_dict_2[row_data[0]].append([row_data[1], row_data[2]])

        return full_dict_2

    def parse_all_const(self, filename, name, target_def, target_type):
        """

        :param name: name of the shape
        :param target_type: indicates the target type of the shape, e.g., class or node
        :param target_def: target definition of the shape
        :param filename: file path
        :return: all constraints belonging to the shape
        """

        cons_dict = self.to_dict(filename)
        trav_dict = {}
        exp_dict = {}

        trav_dict['name'] = name
        trav_dict['target_def'] = target_def
        trav_dict['target_type'] = target_type

        for item in self.chunks({i: j for i, j in cons_dict.items()}, 1):
            for dk, dv in item.items():
                if type(dk) is not tuple:

                    trav_dict['min'] = None
                    trav_dict['max'] = None
                    trav_dict['value'] = None
                    trav_dict['path'] = None
                    trav_dict['shape'] = None
                    trav_dict['datatype'] = None
                    trav_dict['negated'] = None

                    for i in dv:
                        if 'path' in str(i[0]).lower():
                            trav_dict['path'] = str(i[1]).split('_')[0]

                        if 'min' in str(i[0]).lower():
                            trav_dict['min'] = str(i[1]).split('_')[0]

                        if 'max' in str(i[0]).lower():
                            trav_dict['max'] = str(i[1]).split('_')[0]

                        if 'datatype' in str(i[0]).lower():
                            trav_dict['datatype'] = str(i[1]).split('_')[0]

                        if 'valueshape' in str(i[0]).lower():
                            if 'value' in str(i[1][0]).lower():
                                trav_dict['value'] = str(i[1][1])

                            if 'node' in str(i[1][0]).lower():
                                trav_dict['shape'] = str(i[1][1])

                        if 'not' in str(i[0]).lower():
                            trav_dict['negated'] = str(i[1]).split('_')[0]

                exp_dict[str(dk)] = trav_dict.copy()

        return exp_dict

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

    def parse_constraints_ttl(self, array, target_def, constraints_id):
        """
        Parses all constraints of a shape.

        :param array: list of constraints belonging to the shape
        :param target_def: the target definition of the shape
        :param constraints_id: suffix for the constraint IDs
        :return: list of constraints in internal constraint representation
        """
        var_generator = VariableGenerator()
        return [self.parse_constraint(var_generator, array[i], constraints_id + "_c" + str(i + 1), target_def)
                for i in range(len(array))]

    @staticmethod
    def parse_constraint(var_generator, obj, id_, target_def):
        """
        Parses one constraint to the internal representation.

        :param var_generator: reference to the VariableGenerator instance for variable generation for SPARQL queries
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


        if urlparse(shape_ref).netloc != '' and shape_ref is not None:  # if the shape reference is a url, add '<>' to it
            o_shape_ref = '<' + shape_ref + '>'

        if urlparse(value).netloc != '' and value is not None:  # if the value reference is a url, add '<>' to it
            o_value = '<' + value + '>'

        if urlparse(datatype).netloc != '' and datatype is not None:  # if the data type is a url, add '<>' to it
            o_datatype = '<' + datatype + '>'

        if o_path is not None:
            if o_min is not None:
                if o_max is not None:
                    return MinMaxConstraint(var_generator, id_, o_path, o_min, o_max, o_neg, o_datatype, o_value,
                                            o_shape_ref, target_def)
                return MinOnlyConstraint(var_generator, id_, o_path, o_min, o_neg, o_datatype, o_value, o_shape_ref,
                                         target_def)
            if o_max is not None:
                return MaxOnlyConstraint(var_generator, id_, o_path, o_max, o_neg, o_datatype, o_value, o_shape_ref,
                                         target_def)
