#!/usr/bin/env python3
from setuptools import setup

with open('VERSION', 'r', encoding='utf-8') as ver:
    version = ver.read()

with open('README.md', 'r', encoding='utf-8') as fh:
    long_description = fh.read()

setup(
    name='TravSHACL',
    version=version,
    packages=['TravSHACL', 'TravSHACL.constraints', 'TravSHACL.core', 'TravSHACL.rule_based_validation', 'TravSHACL.sparql', 'TravSHACL.utils'],
    license='GNU/GPLv3',
    author='Mónica Figuera, Philipp D. Rohde',
    author_email='philipp.rohde@tib.eu',
    url='https://github.com/SDM-TIB/Trav-SHACL',
    project_urls={
        'Documentation': 'https://sdm-tib.github.io/Trav-SHACL/',
        'Changes': 'https://sdm-tib.github.io/Trav-SHACL/changelog.html',
        'Source Code': 'https://github.com/SDM-TIB/Trav-SHACL',
        'Issue Tracker': 'https://github.com/SDM-TIB/Trav-SHACL/issues'
    },
    download_url='https://github.com/SDM-TIB/Trav-SHACL/archive/refs/tags/v' + version + '.tar.gz',
    description='A SHACL validator capable of planning the traversal and execution of the validation of a shape schema to detect violations early.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    install_requires=['SPARQLWrapper>=2.0.0', 'rdflib>=6.1.1'],
    python_requires='>=3.8',
    classifiers=[
        'Development Status :: 5 - Production/Stable ',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: OS Independent',
        'Intended Audience :: Science/Research'
      ]
)
