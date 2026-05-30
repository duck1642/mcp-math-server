# -*- coding: utf-8 -*-
"""
tests/test_serialization.py - Automated tests for mathematical type serialization.
"""

import json
import pytest
import sympy as sp
import numpy as np
from pint import Quantity
from core.serialization import clean_object

def test_sympy_types_serialization():
    """Asserts that SymPy numbers are converted to serializable float/int."""
    # 1. SymPy One/Integer
    val_int = sp.sin(sp.pi / 2)
    cleaned_int = clean_object(val_int)
    assert isinstance(cleaned_int, int)
    assert cleaned_int == 1
    assert json.dumps(cleaned_int) == "1"

    # 2. SymPy Float
    val_float = sp.sin(3.141592653589793 / 2)
    cleaned_float = clean_object(val_float)
    assert isinstance(cleaned_float, float)
    assert pytest.approx(cleaned_float) == 1.0
    assert json.dumps(cleaned_float) == "1.0"

    # 3. SymPy Complex / Symbolic
    val_complex = sp.I
    cleaned_complex = clean_object(val_complex)
    assert isinstance(cleaned_complex, str)
    assert cleaned_complex == "I"

def test_numpy_types_serialization():
    """Asserts that NumPy scalar and array types are converted to standard float/int/list."""
    # 1. NumPy Float
    np_float = np.float64(3.14)
    cleaned_float = clean_object(np_float)
    assert isinstance(cleaned_float, float)
    assert cleaned_float == 3.14

    # 2. NumPy Integer
    np_int = np.int32(42)
    cleaned_int = clean_object(np_int)
    assert isinstance(cleaned_int, int)
    assert cleaned_int == 42

    # 3. NumPy Array
    np_arr = np.array([1.0, 2.5, 3.0])
    cleaned_arr = clean_object(np_arr)
    assert isinstance(cleaned_arr, list)
    assert cleaned_arr == [1.0, 2.5, 3.0]
    assert json.dumps(cleaned_arr) == "[1.0, 2.5, 3.0]"

def test_complex_serialization():
    """Asserts that complex numbers are converted to string or float if pure real."""
    # 1. Non-zero imaginary part
    c_num = complex(2, 3)
    cleaned_c = clean_object(c_num)
    assert isinstance(cleaned_c, str)
    assert cleaned_c == "(2+3j)"

    # 2. Zero imaginary part
    c_real = complex(5.5, 0)
    cleaned_r = clean_object(c_real)
    assert isinstance(cleaned_r, float)
    assert cleaned_r == 5.5

def test_nested_collection_serialization():
    """Asserts that nested containers are cleaned and fully serializable."""
    data = {
        "status": "success",
        "value": sp.sin(3.141592653589793 / 2),
        "solutions": [np.float64(1.0), sp.sin(sp.pi/2)],
        "vector": np.array([1, 2]),
        "complex_val": complex(1, -1),
        "complex_pure_real": complex(42.0, 0.0),
    }
    
    cleaned = clean_object(data)
    
    # Assert type checks on final output
    assert isinstance(cleaned["value"], float)
    assert isinstance(cleaned["solutions"][0], float)
    assert isinstance(cleaned["solutions"][1], int)
    assert isinstance(cleaned["vector"], list)
    assert isinstance(cleaned["complex_val"], str)
    assert isinstance(cleaned["complex_pure_real"], float)
    
    # Assert successful JSON dumps without exception
    serialized = json.dumps(cleaned)
    assert "success" in serialized
    assert "42.0" in serialized
    assert "(1-1j)" in serialized
