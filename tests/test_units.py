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


def test_metric_prefix_double_scaling_regression():
    """Asserts that input units with metric prefixes are not scaled twice during calculations."""
    # 1. 1 mm (evaluated as 0.001 m in SI calculations) should format back to 1.0 mm (not 1e-6 m)
    res_mm = format_result(0.001, ureg.Quantity(1, ureg.millimeter))
    assert res_mm["value"] == 1.0
    assert res_mm["unit"] == "mm"
    assert "1.0 mm" in res_mm["result_pretty"]
    assert "0.001 m" in res_mm["result_si"]

    # 2. 1 cm (evaluated as 0.01 m in SI calculations) should format back to 1.0 cm (not 0.0001 m)
    res_cm = format_result(0.01, ureg.Quantity(1, ureg.centimeter))
    assert res_cm["value"] == 1.0
    assert res_cm["unit"] == "cm"
    assert "1.0 cm" in res_cm["result_pretty"]
    assert "0.01 m" in res_cm["result_si"]

    # 3. 1234 mm (evaluated as 1.234 m in SI calculations) should format back to 1234.0 mm
    res_1234 = format_result(1.234, ureg.Quantity(1234, ureg.millimeter))
    assert res_1234["value"] == 1234.0
    assert res_1234["unit"] == "mm"
    assert "1234.0 mm" in res_1234["result_pretty"]
    assert "1.234 m" in res_1234["result_si"]

    # 4. Output unit conversion: 1 m -> converted to mm should return 1000.0 mm
    res_output = format_result(1.0, ureg.Quantity(1, ureg.meter), output_unit_str="mm")
    assert res_output["value"] == 1000.0
    assert res_output["unit"] == "mm"
    assert "1000.0 mm" in res_output["result_pretty"]
    assert "1.0 m" in res_output["result_si"]


def test_offset_temperatures_parsing_and_conversion():
    """Asserts that absolute/offset temperature units (degC, degF) parse and convert to kelvins successfully."""
    # 1. 25 degC -> absolute Celsius temperature parses and converts to Kelvin base SI
    q_c = parse_quantity("25 degC")
    assert q_c.magnitude == 25
    assert q_c.units == ureg.degree_Celsius
    assert pytest.approx(q_c.to_base_units().magnitude) == 298.15

    # 2. 25.5 degF -> absolute Fahrenheit temperature parses and converts to Kelvin base SI
    q_f = parse_quantity("25.5 degF")
    assert q_f.magnitude == 25.5
    assert q_f.units == ureg.degree_Fahrenheit
    assert pytest.approx(q_f.to_base_units().magnitude) == 269.5388888888889

    # 3. delta temperature (delta_degC) still parses correctly as multiplicative unit
    q_delta = parse_quantity("10 delta_degC")
    assert q_delta.magnitude == 10
    assert q_delta.units == ureg.delta_degree_Celsius
    assert q_delta.to_base_units().magnitude == 10

    # 4. Reconstruct absolute temperature conversions through format_result (25 degC -> K)
    res_t1 = format_result(298.15, q_c, output_unit_str="K")
    assert pytest.approx(res_t1["value"]) == 298.15
    assert res_t1["unit"] == "K"
    assert "298.15 K" in res_t1["result_pretty"]

    # 5. Reconstruct absolute temperature without target unit (expected to preserve original unit degC)
    res_t2 = format_result(298.15, q_c)
    assert pytest.approx(res_t2["value"]) == 25.0
    assert "C" in res_t2["unit"]
    assert "25.0" in res_t2["result_pretty"]
