# -*- coding: utf-8 -*-
import os

def openFile(path, fileName):
    if not os.path.exists(path):
        os.makedirs(path)
    return open(path + fileName, "w")

def closeFile(file):
    file.close()
