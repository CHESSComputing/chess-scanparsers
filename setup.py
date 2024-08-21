#!/usr/bin/env python
"""
Standard python setup.py file
to build     : python setup.py build
to install   : python setup.py install --prefix=<some dir>
to clean     : python setup.py clean
to build doc : python setup.py doc
to run tests : python setup.py test
"""

# System modules
import os
import setuptools

# [set version]
version = 'PACKAGE_VERSION'
# [version set]

with open('README.md', 'r') as fh:
    long_description = fh.read()

setuptools.setup(
    name='chess_scanparsers',
    version=version,
    author='Keara Soloway, Rolf Verberg',
    author_email='',
    description='Utilities for parsing data and metadata for CHESS scans.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/CHESSComputing/chess-scanparsers',
    packages=['chess_scanparsers'],
    package_dir={'chess_scanparsers': 'chess_scanparsers'},
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.8',
    install_requires=[
        'certif-pyspec'
    ],
)
