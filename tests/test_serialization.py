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


def test_serialization_formatting_options():
    """Asserts that precision rounding and scientific notation conversion format floats correctly."""
    # 1. Standard float with precision
    f_val = 3.14159265
    res_prec = clean_object(f_val, precision=4)
    assert res_prec == 3.1416

    # 2. Standard float with scientific notation
    res_sci = clean_object(f_val, scientific=True)
    assert "3.14159" in res_sci

    # 3. Standard float with both precision and scientific
    res_both = clean_object(f_val, precision=3, scientific=True)
    assert res_both == "3.142e+00"

    # 4. Nested structures formatting
    data = {
        "mag": np.float64(0.000123456),
        "vector": np.array([3.14159, 2.71828]),
        "sym": sp.Float(1.23456)
    }
    cleaned = clean_object(data, precision=2, scientific=True)
    assert cleaned["mag"] == "1.23e-04"
    assert cleaned["vector"] == ["3.14e+00", "2.72e+00"]
    assert cleaned["sym"] == "1.23e+00"
