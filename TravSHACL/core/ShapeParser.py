# -*- coding: utf-8 -*-
__author__ = 'Monica Figuera and Philipp D. Rohde'

import json
import os
from urllib.parse import urlparse

import collections
import rdflib.term
from rdflib import Graph
from itertools import islice

from TravSHACL.constraints.SPARQLConstraint import SPARQLConstraint
from TravSHACL.core.Shape import Shape
from TravSHACL.utils.VariableGenerator import VariableGenerator
from TravSHACL.constraints.MaxOnlyConstraint import MaxOnlyConstraint
from TravSHACL.constraints.MinOnlyConstraint import MinOnlyConstraint

QUERY_TARGET_QUERY = '''SELECT ?query WHERE {{
  <{shape}> a <http://www.w3.org/ns/shacl#NodeShape> ;
      <http://www.w3.org/ns/shacl#targetQuery> ?query .
}}'''


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
        :param use_selective_queries: indicates whether selective queries are used
        :param max_split_size: maximum number of instances per query
        :param order_by_in_queries: indicates whether to use the ORDER BY clause
        :return: list of Shapes parsed from the files
        """
        file_extension = self.get_file_extension(shape_format)
        files_abs_paths = []

        # r=root, f=files, ignoring subdirectories
        for r, _, f in os.walk(path):
            for file in f:
                file_path = os.path.join(r, file)
                if file_extension == os.path.splitext(file_path)[1].lower():
                    files_abs_paths.append(file_path)

        if not files_abs_paths:
            raise FileNotFoundError(path + ' does not contain any shapes of the format ' + shape_format)

        if shape_format == 'JSON':
            return [self.parse_json(
                path=p,
                use_selective_queries=use_selective_queries,
                max_split_size=max_split_size,
                order_by_in_queries=order_by_in_queries
            ) for p in files_abs_paths]
        if shape_format == 'SHACL':
            shapes = []
            [shapes.extend(self.parse_ttl(
                shapes_graph=Graph().parse(p),
                use_selective_queries=use_selective_queries,
                max_split_size=max_split_size,
                order_by_in_queries=order_by_in_queries
            )) for p in files_abs_paths]
            return shapes
        else:
            print('Unexpected format: ' + shape_format)

    @staticmethod
    def get_file_extension(shape_format):
        if shape_format == 'SHACL':
            return '.ttl'
        else:
            return '.json'  # dot added for convenience

    def parse_json(self, path, use_selective_queries, max_split_size, order_by_in_queries):
        """
        Parses a particular file and converts its content into the internal representation of a SHACL shape.

        :param path: the path to the shapes file
        :param use_selective_queries: indicates whether selective queries are used
        :param max_split_size: maximum number of instances per query
        :param order_by_in_queries: indicates whether to use the ORDER BY clause
        :return: Shape object representing the parsed SHACL shape
        """
        target_query = None
        target_type = None

        file = open(path, 'r')
        obj = json.load(file)
        target_def = obj.get('targetDef')
        name = obj['name']
        id_ = name + '_d1'  # str(i + 1) but there is only one set of conjunctions
        constraints = self.parse_constraints(obj['constraintDef']['conjunctions'], target_def, id_)

        include_sparql_prefixes = self.abbreviated_syntax_used(constraints)
        prefixes = None
        if 'prefix' in obj.keys():
            prefixes = obj['prefix']
        referenced_shapes = self.shape_references(obj['constraintDef']['conjunctions'][0])
        valid_flag = [False]   # for json files, the 'or' operations can be implemented starting from here

        if target_def is not None:
            target_query = target_def['query']

            target_def_copy = target_def.copy()
            del target_def_copy['query']
            target_type = list(target_def_copy.keys())[0]

            if urlparse(target_def[target_type]).netloc != '':  # if the target node is a url, add '<>' to it
                target_def = '<' + target_def[target_type] + '>'
            else:
                target_def = target_def[target_type]

        return Shape(name, target_def, target_type, target_query, constraints, id_, referenced_shapes,
                     use_selective_queries, max_split_size, order_by_in_queries, include_sparql_prefixes,
                     valid_flag, prefixes)

    def parse_ttl(self, shapes_graph: Graph, use_selective_queries, max_split_size, order_by_in_queries):
        """
        Parses a particular file and converts its content into the internal representation of a SHACL shape.

        :param shapes_graph: RDFlib graph containing the shapes
        :param use_selective_queries: indicates whether selective queries are used
        :param max_split_size: maximum number of instances per query
        :param order_by_in_queries: indicates whether to use the ORDER BY clause
        :return: Shape object representing the parsed SHACL shape
        """
        queries = self.get_QUERY()
        shapes = []

        names = [str(row[0]) for row in shapes_graph.query(queries[0])]

        for name in names:
            id_ = name + '_d1'  # str(i + 1) but there is only one set of conjunctions

            # to get the target_ref and target_type
            target_def = None
            target_type = None
            if len(shapes_graph.query(queries[1].format(shape=name))) != 0:
                for res in shapes_graph.query(queries[1].format(shape=name)):
                    target_def = str(res[0])
                    target_type = 'class'
                    break
            elif len(shapes_graph.query(queries[2].format(shape=name))) != 0:
                for res in shapes_graph.query(queries[2].format(shape=name)):
                    target_def = str(res[0])
                    target_type = 'node'
                    break

            target_query = None
            if target_def is not None and target_type == 'class':
                for res in shapes_graph.query(QUERY_TARGET_QUERY.format(shape=name)):
                    target_query = str(res[0])
                if target_query is None:
                    target_query = 'SELECT ?x WHERE { ?x a <' + target_def + '> }'  # come up with a query for this
                    if urlparse(target_def).netloc != '':  # if the target node is a url, add '<>' to it
                        target_def = '<' + target_def + '>'

            cons_dict = self.parse_all_const(shapes_graph, name=name, target_def=target_def, target_type=target_type,
                                             query=queries)
            const_array = list(cons_dict.values())  # change the format to an array

            #valid_flag = [entry['flag'] for entry in const_array if entry['flag']]
            valid_flag = []
            for entry in const_array:
                if 'flag' in entry.keys():
                    valid_flag.append(entry['flag'])

            constraints = self.parse_constraints_ttl(const_array, target_def, id_)
            include_sparql_prefixes = self.abbreviated_syntax_used(constraints)
            prefixes = None
            referenced_shapes = self.shape_references(const_array)

            # helps to navigate the shape.__compute_target_queries function
            referenced_shape = {'<' + key + '>': '<' + referenced_shapes[key] + '>'
                                for key in referenced_shapes.keys()
                                if urlparse(referenced_shapes[key]).netloc != ''}

            # to helps to navigate the ShapeSchema.compute_edges function
            if urlparse(name).netloc != '':
                name_ = '<' + name + '>'
            else:
                name_ = name

            shapes.append(Shape(name_, target_def, target_type, target_query, constraints, id_, referenced_shape,
                                use_selective_queries, max_split_size, order_by_in_queries, include_sparql_prefixes,
                                valid_flag, prefixes))

        return shapes

    @staticmethod
    def abbreviated_syntax_used(constraints):
        """
        Run after parsingConstraints.
        Returns false if the constraints' predicates are using absolute paths instead of abbreviated ones
        :param constraints: all shape constraints
        :return: True if prefix notation is used, False otherwise
        """
        for c in constraints:
            if c.path is not None and (c.path.startswith('<') and c.path.endswith('>')):
                return False
        return True

    @staticmethod
    def shape_references(constraints):
        """
        Gets the shapes referenced by the given constraints.

        :param constraints: the constraints to get the referenced shapes for
        :return: Python dictionary with the referenced shapes and the path referencing the shape
        """
        return {c.get('shape'): c.get('path') for c in constraints if c.get('shape') is not None}

    @staticmethod
    def chunks(datei, SIZE):
        """
        Break down list of input (dictionaries) into individual dictionaries

        :param datei: list of input to be broken down
        :param SIZE: tells the length or size for each output
        :return: inputs divided in len(SIZE)
        """
        it = iter(datei)
        for i in range(0, len(datei), SIZE):
            yield {k: datei[k] for k in islice(it, SIZE)}

    @staticmethod
    def get_QUERY():
        QUERY_SHAPES = '''SELECT DISTINCT ?shape WHERE {
            ?shape a <http://www.w3.org/ns/shacl#NodeShape> .
            }'''

        QUERY_TARGET_1 = '''SELECT ?target WHERE {{
            <{shape}> a <http://www.w3.org/ns/shacl#NodeShape> .
            <{shape}> <http://www.w3.org/ns/shacl#targetClass> ?target .
        }}
        '''

        QUERY_TARGET_2 = '''SELECT ?target WHERE {{
                    <{shape}> a <http://www.w3.org/ns/shacl#NodeShape> .
                    <{shape}> <http://www.w3.org/ns/shacl#targetNode> ?target .
                }}
                '''

        QUERY_CONSTRAINTS = '''SELECT ?constraint WHERE {{
          <{shape}> a <http://www.w3.org/ns/shacl#NodeShape> .
          <{shape}> <http://www.w3.org/ns/shacl#property> ?constraint .
        }}
        '''

        QUERY_CONSTRAINT_DETAILS = '''SELECT ?p ?o WHERE {{
            {{
                ?s ?p ?o .
                FILTER( str(?s) = "{constraint}" )
                FILTER( ?p != <http://www.w3.org/ns/shacl#path> || !isBlank(?o) )
            }} UNION {{
                ?s <http://www.w3.org/ns/shacl#path>/<http://www.w3.org/ns/shacl#inversePath> ?o .
                BIND(<http://www.w3.org/ns/shacl#path> AS ?p)
                BIND(CONCAT('^', str(?o)) AS ?o)
                FILTER( str(?s) = "{constraint}" )
            }}
        }}'''

        QUERY_QVS_REF_1 = '''SELECT ?shape_ref WHERE {{
              ?s <http://www.w3.org/ns/shacl#node> ?shape_ref .
              FILTER ( str(?s) = "{qvs}" )
            }}'''

        QUERY_QVS_REF_2 = '''SELECT ?shape_ref WHERE {{
                  ?s <http://www.w3.org/ns/shacl#value> ?shape_ref .
                  FILTER ( str(?s) = "{qvs}" )
                }}'''

        QUERY_SPARQL_CONSTRAINTS = '''SELECT ?constraint ?query WHERE {{
          <{shape}> a <http://www.w3.org/ns/shacl#NodeShape> .
          <{shape}> <http://www.w3.org/ns/shacl#sparql> ?constraint .
          ?constraint <http://www.w3.org/ns/shacl#select> ?query .
        }}
        '''

        QUERY_OR = '''SELECT ?constraint WHERE {{
                                  <{shape}> a <http://www.w3.org/ns/shacl#NodeShape> .
                                  <{shape}> <http://www.w3.org/ns/shacl#or> ?constraint .
                                }}
                                '''
        return QUERY_SHAPES, QUERY_TARGET_1, QUERY_TARGET_2, QUERY_CONSTRAINTS, QUERY_CONSTRAINT_DETAILS, \
               QUERY_QVS_REF_1, QUERY_QVS_REF_2, QUERY_SPARQL_CONSTRAINTS, QUERY_OR

    def get_res(self, filename, name, query):
        """

        :param query: List of queries
        :param name: name of the Shape
        :param filename: shape file in ttl format
        :return: valid response from query execution
        """
        exp_dict = collections.defaultdict(list)
        if filename.query(query[3].format(shape=name)):
            for constraint in filename.query(query[3].format(shape=name)):
                constraint_id = constraint[0]

                for detail in filename.query(query[4].format(constraint=constraint_id)):

                    if isinstance(detail.asdict()['o'], rdflib.term.BNode):
                        qv_type = detail.asdict()['p']
                        qvs = detail.asdict()['o']
                        if len(filename.query(query[5].format(qvs=qvs))) != 0:
                            for shape_ref in filename.query(query[5].format(qvs=qvs)):
                                # dict_1 = [qv_type, ['shape', str(shape_ref.asdict()['shape_ref'])]]
                                dict_1 = [qv_type, str(shape_ref.asdict()['shape_ref'])]
                            exp_dict[str(constraint_id)].append(dict_1.copy())
                        else:
                            for shape_ref in filename.query(query[6].format(qvs=qvs)):
                                dict_1 = [qv_type, ['value', str(shape_ref.asdict()['shape_ref'])]]
                            exp_dict[str(constraint_id)].append(dict_1.copy())
                    else:
                        # detail_dict = detail.asdict()
                        dict_2 = [str(detail['p']), str(detail['o'])]
                        exp_dict[str(constraint_id)].append(dict_2.copy())

        if filename.query(query[8].format(shape=name)):
            for constraint in filename.query(query[8].format(shape=name)):
                constraint_id = filename.items(constraint[0])
                dict_or = collections.defaultdict(list)
                for item in constraint_id:
                    for detail in filename.query(query[4].format(constraint=item.toPython())):
                        dict_3 = [str(detail['p']), str(detail['o'])]
                        dict_or[str(item)].append(dict_3.copy())
                exp_dict[str(constraint_id)].append(dict_or.copy())

        return exp_dict

    def parse_all_const(self, filename, name, target_def, target_type, query):
        """

        :param query: List of queries
        :param name: name of the shape
        :param target_type: indicates the target type of the shape, e.g., class or node
        :param target_def: target definition of the shape
        :param filename: file path
        :return: all constraints belonging to the shape
        """
        cons_dict = self.get_res(filename, name, query)
        trav_dict = {}
        exp_dict = {}

        trav_dict['name'] = name
        trav_dict['target_def'] = target_def
        trav_dict['target_type'] = target_type

        # SPARQL constraints first
        for result in filename.query(query[7].format(shape=name)):
            trav_dict['sparql'] = result['query'].toPython()
            exp_dict[str(result['constraint'].toPython())] = trav_dict.copy()

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
                    trav_dict['or'] = {}
                    trav_dict['flag'] = False

                    if "Graph.items" not in dk:
                        for i in dv:
                            if 'path' in str(i[0]).lower():
                                trav_dict['path'] = str(i[1])

                            if 'min' in str(i[0]).lower():
                                trav_dict['min'] = str(i[1])

                            if 'max' in str(i[0]).lower():
                                trav_dict['max'] = str(i[1])

                            if 'datatype' in str(i[0]).lower():
                                trav_dict['datatype'] = str(i[1])

                            if 'valueshape' in str(i[0]).lower():
                                trav_dict['shape'] = str(i[1])
                            #                            if 'value' in str(i[1][0]).lower():
                            #                                trav_dict['value'] = str(i[1][1])
                            #                            if 'shape' in str(i[1][0]).lower():
                            #                                trav_dict['shape'] = str(i[1][1])

                            if 'not' in str(i[0]).lower():
                                trav_dict['negated'] = str(i[1])

                    else:
                        trav_dict['flag'] = True
                        for options in dv:
                            for i_or, j_or in options.items():
                                trav_dict['or'][i_or] = {}
                                for j_sub in j_or:
                                    if 'path' in str(j_sub[0]).lower():
                                        trav_dict['or'][i_or]['path'] = str(j_sub[1])
                                    if 'max' in str(j_sub[0]).lower():
                                        trav_dict['or'][i_or]['max'] = str(j_sub[1])
                                        # trav_dict['max'] = str(sub_option[1])
                                    if 'min' in str(j_sub[0]).lower():
                                        trav_dict['or'][i_or]['min'] = str(j_sub[1])

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
        constraints = []
        options = None
        [constraints.extend(self.parse_constraint(var_generator, array[0][i], constraints_id + '_c' + str(i + 1),
                                                  target_def, options)) for i in range(len(array[0]))]
        return constraints

    def parse_constraints_ttl(self, array, target_def, constraints_id):
        """
        Parses all constraints of a shape.

        :param array: list of constraints belonging to the shape
        :param target_def: the target definition of the shape
        :param constraints_id: suffix for the constraint IDs
        :return: list of constraints in internal constraint representation
        """
        var_generator = VariableGenerator()
        constraints = []

        for i, constraint in enumerate(array):
            if constraint.get('flag'):
                or_constraints = []
                for key in constraint['or'].keys():
                    sub_constraint = constraint['or'][key]
                    or_constraints.extend(self.parse_constraint(var_generator, sub_constraint, constraints_id + '_c' + str(i + 1), target_def, None))
                constraints.extend(self.parse_constraint(var_generator, constraint, constraints_id + '_c' + str(i + 1), target_def, or_constraints))
            else:
                constraints.extend(self.parse_constraint(var_generator, constraint, constraints_id + '_c' + str(i + 1), target_def, None))

        return constraints

    @staticmethod
    def parse_constraint(var_generator, obj, id_, target_def, options=None):
        """
        Parses one constraint to the internal representation.

        :param var_generator: reference to the VariableGenerator instance for variable generation for SPARQL queries
        :param obj: the constraint in its original representation
        :param id_: suffix for the constraint ID
        :param target_def: the target definition of the associated shape
        :param options: contains Constraints for or_operation
        :return: constraint in internal representation
        """
        min_ = obj.get('min')
        max_ = obj.get('max')
        shape_ref = obj.get('shape')
        datatype = obj.get('datatype')
        value = obj.get('value')
        path = obj.get('path')
        negated = obj.get('negated')
        query = obj.get('sparql')

        if path is not None and str(path).startswith('^'):
            is_inverse_path = True
            path = str(path)[1:]
        else:
            is_inverse_path = False

        o_min = None if (min_ is None) else int(min_)
        o_max = None if (max_ is None) else int(max_)
        o_shape_ref = None if (shape_ref is None) else str(shape_ref)
        o_datatype = None if (datatype is None) else str(datatype)
        o_value = None if (value is None) else str(value)
        o_path = None if (path is None) else str(path)
        o_neg = True if (negated is None) else not negated  # True means it is a positive constraint
        o_query = None if (query is None) else str(query)

        if path is not None and urlparse(path).netloc != '':  # if the predicate is a url, add '<>' to it
            o_path = '<' + path + '>'
        if is_inverse_path:
            o_path = '^' + o_path

        if urlparse(
                shape_ref).netloc != '' and shape_ref is not None:  # if the shape reference is a url, add '<>' to it
            o_shape_ref = '<' + shape_ref + '>'

        if urlparse(value).netloc != '' and value is not None:  # if the value reference is a url, add '<>' to it
            o_value = '<' + value + '>'

        if urlparse(datatype).netloc != '' and datatype is not None:  # if the data type is a url, add '<>' to it
            o_datatype = '<' + datatype + '>'

        if o_path is not None:
            if o_min is not None:
                if o_max is not None:
                    return [MinOnlyConstraint(var_generator, id_, o_path, o_min, o_neg, options, o_datatype, o_value, o_shape_ref, target_def),
                            MaxOnlyConstraint(var_generator, id_, o_path, o_max, o_neg, options, o_datatype, o_value, o_shape_ref, target_def)]
                return [MinOnlyConstraint(var_generator, id_, o_path, o_min, o_neg, options, o_datatype, o_value, o_shape_ref, target_def)]
            if o_max is not None:
                return [MaxOnlyConstraint(var_generator, id_, o_path, o_max, o_neg, options, o_datatype, o_value, o_shape_ref, target_def)]
        elif o_query is not None:
            return [SPARQLConstraint(id_, o_neg, o_query)]
        elif o_path is None:
            return [MinOnlyConstraint(var_generator, id_, o_path, o_min, o_neg, options, o_datatype, o_value, o_shape_ref, target_def)]
