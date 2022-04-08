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
            #print("Unexpected format: " + shape_format)

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
        target_ref = name[0][1]

        # to get the target_ref and target_type
        data_type = self.get_targetdef(g_file, name[0][0], target_ref)
        if data_type[0] is not None:
            target_def = data_type[0]
            target_type = 'Class'
        elif data_type[1] is not None:
            target_def = data_type[1]
            target_type = 'Node'
        else:
            target_def = None
            target_type = None

        const_list = ['minCount', 'maxCount', 'qualifiedValueShape', 'qualifiedMinCount',
                      'qualifiedMaxCount', 'datatype', 'not']

        cons_dict = self.parse_all_const(g_file, constraint=const_list, name=name[0][0], target_ref=target_ref,
                                         target_def=target_def, target_type=target_type)

        const_array = list(cons_dict.values())  # change the format to an array
        constraints = self.parse_constraints_ttl(const_array, target_def, id_)

        include_sparql_prefixes = self.abbreviated_syntax_used(constraints)
        prefixes = None
        referenced_shapes = self.shape_references(const_array)
        target_query = None

        return Shape(name[0][0], target_def, target_type, target_query, constraints, id_, referenced_shapes,
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

        :param filename: file to be processed
        :return: the main shape
        """
        query = '''
                SELECT ?sub ?obj WHERE { 
                ?sub a ?obj. }
            '''

        return [[str(row.asdict()['sub'].toPython()), str(row.asdict()['obj'].toPython())]
                       for row in filename.query(query)]

    @staticmethod
    def get_targetdef(filename, sub_ref, obj_ref):
        """
        extract the subject of the main shape

        :param filename:
        :param obj_ref: the target object for the main shape
        :param sub_ref:
        :return: the target node or  target class
        """

        type_list = ['targetClass', 'targetNode']
        datatype = []
        select_stat = 'SELECT ?target WHERE { :'
        top_q = ' a sh:'
        mid = '; sh:'
        close = ' ?target. }'

        for i in type_list:
            query_td = select_stat + str(sub_ref).split('/')[-1] + top_q + str(obj_ref).split('#')[-1] + mid + i + close
            target_def = filename.query(query_td)
            if len(target_def) != 0:
                for row in target_def:
                    d_type = str(row.asdict()['target'].toPython())
                    datatype.append(d_type.split('/')[-1])
            else:
                datatype.append(None)

        return datatype

    @staticmethod
    def querylist(constraint, name, target_ref):
        """

        :param name:
        :param constraint: list of constraints
        :param target_ref: the target object for the main shape
        :return: List of 4 queries for each constraint
        """

        query_dict = {}

        # query fragmentation
        select_xy = 'SELECT ?x_data ?y_data WHERE { :'
        select_xzy = 'SELECT ?x_data ?z_data ?y_data WHERE { :'
        select_xya = 'SELECT ?x_data ?y_data ?a_data WHERE { :'
        select_xzya = 'SELECT ?x_data ?z_data ?y_data ?a_data WHERE { :'
        top_part = ' a sh:'
        middle_part_x = ' ; sh:property [ sh:path ?x_data ; sh:'
        middle_part_xz = ' ; sh:property [ sh:path [?x_data ?z_data] ;  sh:'
        end_part_y = ' ?y_data ] .}'
        end_part_ya = ' [?y_data ?a_data] ] .}'

        for i in constraint:
            query3 = select_xy + str(name).split('/')[-1] + top_part + str(target_ref).split('#')[-1] + middle_part_x + i + end_part_y
            query2 = select_xzy + str(name).split('/')[-1] + top_part + str(target_ref).split('#')[-1] + middle_part_xz + i + end_part_y
            query1 = select_xya + str(name).split('/')[-1] + top_part + str(target_ref).split('#')[-1] + middle_part_x + i + end_part_ya
            query0 = select_xzya + str(name).split('/')[-1] + top_part + str(target_ref).split('#')[-1] + middle_part_xz + i + end_part_ya

            query_list = [query0, query1, query2, query3]
            query_dict[i] = query_list

        return query_dict

    def get_query(self, filename, constraint, name, target_ref):
        """

        :param name: Shape name
        :param filename: shape file in ttl format
        :param constraint: list of constraints
        :param target_ref: the target object for the main shape
        :return: list of validated queries
        """
        que_dict = self.querylist(constraint, name, target_ref)
        val_query = collections.defaultdict(list)

        for dk, dv in que_dict.items():
            for i in dv:
                if len(filename.query(i)) != 0:
                    new_query_dict = {dk: i}
                    val_query[dv.index(i)].append(new_query_dict)

        return val_query

    def get_resp(self, filename, constraint, name, target_ref):
        """

        :param name: name of the shape
        :param filename: shape file in ttl format
        :param constraint: list of constraints
        :param target_ref: the target object for the main shape
        :return: valid response from query execution
        """

        query = self.get_query(filename, constraint, name, target_ref)
        full_dict_b = collections.defaultdict(list)  # dictionary for responses including BNode
        val_resp = collections.defaultdict(list)  # dictionary for only valid responses, i.e. without BNode

        # to populate  dictionary with query response
        for dk, dv in query.items():
            for i in dv:
                resp_dict = {}
                for ddk, ddv in i.items():
                    resp_dict[ddk] = filename.query(str(ddv))
                    full_dict_b[dk].append(resp_dict)

        # check for BNode in the responses and remove
        for dk, dv in full_dict_b.items():
            for i in dv:
                for ddk, ddv in i.items():
                    if dk == 3:
                        list1 = []
                        rep = {x: y for x, y in ddv}
                        for dddk, dddv in rep.items():
                            if type(dddk) is BNode or type(dddv) is BNode:
                                list1.append(dddk)
                        for j in list1:
                            del rep[j]

                        if len(rep) != 0:
                            val_resp[ddk].append(rep)

                    elif dk == 1:
                        list1 = []
                        rep = collections.defaultdict(list)
                        newy = {}
                        for x, y, a in ddv:
                            newy[x] = [y, a]
                            rep[x].append(newy[x])

                        for dddk, dddv in rep.items():
                            if type(dddk) is BNode or type(dddv) is BNode:
                                list1.append(dddk)
                        for j in list1:
                            del rep[j]
                        if len(rep) != 0:
                            val_resp[ddk].append(rep)

                    elif dk == 2:
                        list1 = []
                        rep = {(x, z): y for x, z, y in ddv}
                        for dddk, dddv in rep.items():
                            if type(dddk) is BNode or type(dddv) is BNode:
                                list1.append(dddk)
                        for j in list1:
                            del rep[j]
                        if len(rep) != 0:
                            val_resp[ddk].append(rep)

                    elif dk == 0:
                        rep = {(x, z): [y, a] for x, z, y, a in ddv}
                        val_resp[ddk].append(rep)

        return val_resp

    def parse_all_const(self, filename, constraint, name, target_ref, target_def, target_type):
        """

        :param name: name of the shape
        :param target_type: indicates the target type of the shape, e.g., class or node
        :param target_def: target definition of the shape
        :param filename: file path
        :param constraint: the constraints belonging to the shape
        :param target_ref: object definition of the main shape
        :return: all constraints belonging to the shape
        """

        for_iti = self.get_resp(filename, constraint, name, target_ref)

        trav_dict = {}
        shape_dict = {}
        exp_dict = {}

        trav_dict['name'] = name
        trav_dict['target_def'] = target_def
        trav_dict['target_type'] = target_type

        for dk, dv in for_iti.items():
            for abc in dv:
                for k in abc.keys():
                    dl = shape_dict.get(k, [])
                    shape_dict[k] = dl + [dk]

        for item in self.chunks({i: j for i, j in shape_dict.items()}, 1):
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
                        # trav_dict['path'] = str(dk.split('/')[-1])
                        trav_dict['path'] = str(dk)

                        if 'min' in str(i).lower():
                            min_get = for_iti.get(i)

                            for j in min_get:
                                for ddk, ddv in j.items():
                                    if ddk == dk:
                                        trav_dict['min'] = str(ddv)

                        if 'max' in str(i).lower():
                            max_get = for_iti.get(i)

                            for j in max_get:
                                for ddk, ddv in j.items():
                                    if ddk == dk:
                                        trav_dict['max'] = str(ddv)

                        if 'datatype' in str(i).lower():
                            datatype_get = for_iti.get(i)

                            for j in datatype_get:
                                for ddk, ddv in j.items():
                                    if ddk == dk:
                                        trav_dict['datatype'] = str(ddv)

                        if 'valueshape' in str(i).lower():
                            value_get = for_iti.get(i)

                            for j in value_get:
                                for ddk, ddv in j.items():
                                    if ddk == dk:
                                        for r in ddv:
                                            if 'value' in str(r[0]).lower():
                                                # trav_dict['value'] = str(r[1].split('/')[-1])
                                                trav_dict['value'] = str(r[1])
                                            if 'node' in str(r[0]).lower():
                                                # trav_dict['shape'] = str(r[1].split('/')[-1])
                                                trav_dict['shape'] = str(r[1])

                        if 'not' in str(i).lower():
                            not_get = for_iti.get(i)

                            for j in not_get:
                                for ddk, ddv in j.items():
                                    if ddk == dk:
                                        trav_dict['negated'] = str(ddv)
                                        # trav_dict['negated'] = str(ddv.split('/')[-1])

                    exp_dict[str(dk.split('/')[-1])] = trav_dict.copy()
                # implement an else statement if the node constraint is to be used
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


