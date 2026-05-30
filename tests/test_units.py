# -*- coding: utf-8 -*-
"""
tests/test_units.py - Automated tests for the physical unit pipeline.
Asserts that physical units parse, convert, validate, and format correctly.
"""

import pytest
from core.units import (
    parse_quantity,
    parse_substitutions,
    validate_expression_units,
    format_result
)
from core.errors import UnitMismatchError
from core.namespace import ureg

def test_unit_parsing():
    """Asserts that physical units parse correctly into Pint Quantity instances."""
    q1 = parse_quantity("500 N")
    assert q1.magnitude == 500
    assert q1.units == ureg.newton

    q2 = parse_quantity("200 GPa")
    assert q2.magnitude == 200
    assert q2.units == ureg.gigapascal

    # Int/float primitives
    q3 = parse_quantity(15.5)
    assert q3.magnitude == 15.5
    assert q3.dimensionless

    # Undefined units should raise UnitMismatchError
    with pytest.raises(UnitMismatchError):
        parse_quantity("100 blablas")


def test_dimensional_compatibility_checks():
    """Asserts that additions/subtractions between incompatible dimensions raise errors."""
    parsed = parse_substitutions({"F": "500 N", "L": "2 m", "P": "100 Pa"})

    # F * L (Newton * Meter -> Joules) is valid multiplication
    result_qty = validate_expression_units("F * L", parsed)
    assert result_qty.check("[mass] * [length]**2 / [time]**2")

    # F + L (Newton + Meter) is dimensionally incompatible
    with pytest.raises(UnitMismatchError) as exc_info:
        validate_expression_units("F + L", parsed)
    assert "inconsistency" in str(exc_info.value)


def test_transcendental_boundary_checks():
    """Asserts that transcendental functions check that their arguments are dimensionless."""
    # x is an angle (degree) -> converting to radians is dimensionless
    parsed_angle = parse_substitutions({"theta": "30 deg"})
    res_qty = validate_expression_units("sin(theta)", parsed_angle)
    assert res_qty.dimensionless
    assert abs(res_qty.magnitude - 0.5) < 1e-5

    # x has meters -> sin(x) must throw UnitMismatchError
    parsed_len = parse_substitutions({"x": "5 m"})
    with pytest.raises(UnitMismatchError) as exc_info:
        validate_expression_units("sin(x)", parsed_len)
    assert "must be dimensionless" in str(exc_info.value)


def test_format_result():
    """Asserts that result quantities are formatted strictly as plain ASCII to prevent mojibakes."""
    # Force SI formatting: 1000 N * m -> 1000 J
    # Note: to_compact() automatically formats 1000 J to 1.0 kJ
    res = format_result(1000.0, ureg.joule)
    assert res["value"] == 1.0
    assert res["unit"] == "kJ"
    assert "1.0 kJ" in res["result_pretty"]
    assert "kg * m ** 2 / s ** 2" in res["result_si"]

    # Target unit conversion: 1000 J -> 1 kJ
    res_target = format_result(1000.0, ureg.joule, output_unit_str="kJ")
    assert res_target["value"] == 1.0
    assert res_target["unit"] == "kJ"
    assert "1.0 kJ" in res_target["result_pretty"]
