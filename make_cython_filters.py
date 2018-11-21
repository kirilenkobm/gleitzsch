#!/usr/bin/env python3
"""Compile Cython functions.

Run via
./make_cython_filters.py build_ext --inplace
"""
from distutils.core import setup
from Cython.Build import cythonize
import numpy

setup(ext_modules=cythonize("modules/blur_detection.pyx"), include_dirs=[numpy.get_include()])
