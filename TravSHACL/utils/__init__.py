# -*- coding: utf-8 -*-
__author__ = 'Philipp D. Rohde'


def parse_heuristics(input_):
    """
    Parses the heuristics from the arguments passed to Trav-SHACL.

    :param input_: the heuristics argument
    :return: Python dictionary with the heuristics to be used for the evaluation
    """
    heuristics = {}
    if 'TARGET' in input_:
        heuristics['target'] = True
    else:
        heuristics['target'] = False

    if 'IN' in input_:
        heuristics['degree'] = 'in'
    elif 'OUT' in input_:
        heuristics['degree'] = 'out'
    else:
        heuristics['degree'] = False

    if 'SMALL' in input_:
        heuristics['properties'] = 'small'
    elif 'BIG' in input_:
        heuristics['properties'] = 'big'
    else:
        heuristics['properties'] = False

    return heuristics
