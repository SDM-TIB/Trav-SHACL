# -*- coding: utf-8 -*-
__author__ = 'Philipp D. Rohde'

import os


def open_file(path, filename):
    """
    Opens a file with the given filename at the specified path. If the path does not exist, it will be created.
    The file will be opened in write mode with UTF-8 encoding.

    :param path: path where to open the file
    :param filename: name of the file to be opened
    :return: file handler
    """
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)
    return open(os.path.join(path, filename), 'w', encoding='utf8')


def close_file(file):
    """
    Closes the specified file.

    :param file: the File object to close
    """
    file.close()
