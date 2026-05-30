# -*- coding: utf-8 -*-
"""
core/serialization.py - Utility to sanitize mathematical types for JSON serialization.
Converts SymPy, NumPy, Pint, and complex numbers to standard JSON-compatible Python primitives.
"""

from typing import Any
import numpy as np

def clean_object(obj: Any) -> Any:
    """
    Recursively scans and converts custom math types (SymPy, NumPy, complex)
    into JSON-serializable Python native types.
    """
    # 1. Handle None and primitive serializable types directly
    if obj is None or isinstance(obj, (bool, str)):
        return obj

    # 2. Handle SymPy objects
    try:
        import sympy as sp
        if isinstance(obj, sp.Basic):
            if obj.is_Integer:
                return int(obj)
            elif obj.is_Float or obj.is_Rational:
                return float(obj)
            elif obj.is_number:
                # Could be complex or symbolic constant like pi
                try:
                    c = complex(obj)
                    if c.imag == 0:
                        return float(c.real)
                    return str(obj)
                except Exception:
                    return str(obj)
            else:
                return str(obj)
    except ImportError:
        pass

    # 3. Handle NumPy types
    if isinstance(obj, (np.integer, np.int32, np.int64)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float32, np.float64)):
        return float(obj)
    elif isinstance(obj, (np.complexfloating, np.complex64, np.complex128)):
        c = complex(obj)
        if c.imag == 0:
            return float(c.real)
        return str(c)
    elif isinstance(obj, np.ndarray):
        return [clean_object(x) for x in obj.tolist()]

    # 4. Handle Pint Quantity
    try:
        from pint import Quantity
        if isinstance(obj, Quantity):
            return clean_object(obj.magnitude)
    except ImportError:
        pass

    # 5. Handle Python complex numbers
    if isinstance(obj, complex):
        if obj.imag == 0:
            return float(obj.real)
        return str(obj)

    # 6. Handle standard float and int
    if isinstance(obj, (int, float)):
        return obj

    # 7. Handle collections recursively
    if isinstance(obj, dict):
        return {str(k): clean_object(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple, set)):
        return [clean_object(x) for x in obj]

    # Fallback to string representation
    return str(obj)
