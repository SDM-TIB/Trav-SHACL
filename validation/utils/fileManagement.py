# -*- coding: utf-8 -*-

def openFile(path, fileName):
    return open(path + fileName, "w")

def closeFile(file):
    file.close()
