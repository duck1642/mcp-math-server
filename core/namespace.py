# -*- coding: utf-8 -*-
"""
core/namespace.py - Pre-loaded namespace dictionary containing scientific computational libraries.
Allows mathematical evaluations to run with preloaded scientific libraries without manual imports.
"""

import math
import cmath
import sympy as sp
import numpy as np
import scipy
from scipy import linalg, integrate, optimize, signal, fft

import matplotlib
# Force stateless, headless backend for thread-safety and no UI operations
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from pint import UnitRegistry

# Global thread-safe Pint Unit Registry
ureg = UnitRegistry()

# Construct the standard scientific namespace
SCIENCE_NAMESPACE = {
    # Major modules
    "sp": sp,
    "np": np,
    "scipy": scipy,
    "cmath": cmath,
    "math": math,
    "plt": plt,
    
    # SciPy submodules
    "linalg": linalg,
    "integrate": integrate,
    "optimize": optimize,
    "signal": signal,
    "fft": fft,
    
    # Pint unit registry
    "ureg": ureg,
    "u": ureg,  # Convenient shorthand for unit expressions
}

# Expose common mathematical constants and functions directly at the root for ease of use
COMMON_MATH_GLOBALS = {
    # Constants
    "pi": math.pi,
    "pi_sym": sp.pi,
    "e": math.e,
    "I": sp.I,
    "j": 1j,
    
    # Basic math builtins
    "inf": float("inf"),
    "nan": float("nan"),
    
    # Standard mathematical functions (using SymPy to support symbolic variables)
    "sin": sp.sin,
    "cos": sp.cos,
    "tan": sp.tan,
    "asin": sp.asin,
    "acos": sp.acos,
    "atan": sp.atan,
    "sinh": sp.sinh,
    "cosh": sp.cosh,
    "tanh": sp.tanh,
    "log": sp.log,
    "ln": sp.log,
    "exp": sp.exp,
    "sqrt": sp.sqrt,
    "factorial": sp.factorial,
    "gamma": sp.gamma,
}

# Merge all into the final namespace
SCIENCE_NAMESPACE.update(COMMON_MATH_GLOBALS)
