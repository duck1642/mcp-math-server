# -*- coding: utf-8 -*-
"""
core/units.py - Pint-based physical unit validation and dimensional consistency pipeline.
Isolates units from the core symbolic and numerical calculation engine to guarantee safety.
"""

import math
from typing import Any, Dict, List, Optional, Tuple, Union
from pint import Quantity, Unit, DimensionalityError, UndefinedUnitError

from core.namespace import ureg
from core.errors import UnitMismatchError
from core.sandbox import run_sandboxed

def parse_quantity(value: Any) -> Quantity:
    """
    Parses a input value (string, float, int) into a Pint Quantity object.
    Raises UnitMismatchError if parsing fails or unit is undefined.
    """
    if isinstance(value, Quantity):
        return value
        
    if isinstance(value, (int, float, complex)):
        return ureg.Quantity(value)
        
    if isinstance(value, str):
        try:
            # Explicitly parse string to prevent local encoding issues
            return ureg.Quantity(value.strip())
        except (UndefinedUnitError, ValueError, TypeError) as e:
            raise UnitMismatchError(
                f"Failed to parse unit string '{value}': {e}",
                suggestion="Ensure unit symbols are standard Pint notation (e.g. 'N', 'Pa', 'm/s^2', 'kg')."
            )
            
    raise UnitMismatchError(f"Unsupported value type for unit parsing: {type(value)}")


def parse_substitutions(substitutions: Optional[Dict[str, Any]]) -> Dict[str, Quantity]:
    """
    Converts a map of substitution variables to their Pint Quantity representations.
    """
    parsed = {}
    if not substitutions:
        return parsed
        
    for var, val in substitutions.items():
        parsed[var] = parse_quantity(val)
        
    return parsed


# Safe, wrapped transcendental mathematical functions for dimensional analysis
def wrap_checking_transcendental(func_name: str, check_dimensionless: bool = True, allow_angle: bool = False):
    """
    Creates a safe mathematical function wrapper that operates on Pint Quantity instances
    without raising TypeErrors. Enforces dimensional consistency checks.
    """
    math_func = getattr(math, func_name, None)
    
    def wrapper(x: Any) -> Union[Quantity, Any]:
        if isinstance(x, Quantity):
            if check_dimensionless:
                is_angle_unit = False
                if x.units != ureg.dimensionless:
                    try:
                        x.to("radian")
                        is_angle_unit = True
                    except Exception:
                        pass
                        
                if allow_angle and is_angle_unit:
                    val = x.to("radian").magnitude
                elif x.dimensionless:
                    val = x.magnitude
                else:
                    expected = "dimensionless or angle" if allow_angle else "dimensionless"
                    raise UnitMismatchError(
                        f"Argument to mathematical function '{func_name}' must be {expected}. "
                        f"Got physical units: {x.units}."
                    )
            else:
                # E.g. sqrt operates on any units
                if func_name == "sqrt":
                    return x ** 0.5
                val = x.magnitude
                
            res_val = math_func(val) if math_func else 1.0
            # Returns a dimensionless Quantity representing the float output
            return ureg.Quantity(res_val)
        else:
            return math_func(x) if math_func else x
            
    return wrapper


# Mocked structures to replace math, cmath, and numpy modules during unit checking
class WrappedModule:
    """Mock module containing wrapped unit-safe math methods."""
    def __init__(self):
        self.pi = math.pi
        self.e = math.e
        self.sin = wrap_checking_transcendental("sin", check_dimensionless=True, allow_angle=True)
        self.cos = wrap_checking_transcendental("cos", check_dimensionless=True, allow_angle=True)
        self.tan = wrap_checking_transcendental("tan", check_dimensionless=True, allow_angle=True)
        self.asin = wrap_checking_transcendental("asin", check_dimensionless=True, allow_angle=False)
        self.acos = wrap_checking_transcendental("acos", check_dimensionless=True, allow_angle=False)
        self.atan = wrap_checking_transcendental("atan", check_dimensionless=True, allow_angle=False)
        self.sinh = wrap_checking_transcendental("sinh", check_dimensionless=True, allow_angle=False)
        self.cosh = wrap_checking_transcendental("cosh", check_dimensionless=True, allow_angle=False)
        self.tanh = wrap_checking_transcendental("tanh", check_dimensionless=True, allow_angle=False)
        self.exp = wrap_checking_transcendental("exp", check_dimensionless=True, allow_angle=False)
        self.log = wrap_checking_transcendental("log", check_dimensionless=True, allow_angle=False)
        self.log10 = wrap_checking_transcendental("log10", check_dimensionless=True, allow_angle=False)
        self.sqrt = wrap_checking_transcendental("sqrt", check_dimensionless=False)


# Construct checking namespace using wrapped structures
PINT_CHECKING_NAMESPACE: Dict[str, Any] = {
    "math": WrappedModule(),
    "cmath": WrappedModule(),
    "np": WrappedModule(),
    "numpy": WrappedModule(),
    "ureg": ureg,
    "u": ureg,
    "pi": math.pi,
    "e": math.e,
}

# Mount checking math functions directly at root namespace
_math_mod = WrappedModule()
for attr in dir(_math_mod):
    if not attr.startswith("_"):
        PINT_CHECKING_NAMESPACE[attr] = getattr(_math_mod, attr)


def validate_expression_units(expression: str, parsed_subs: Dict[str, Quantity]) -> Quantity:
    """
    Executes expression inside sandboxed checker namespace where variables are Pint Quantities.
    Asserts dimensional consistency and determines final physical output units.
    Raises UnitMismatchError if addition/subtraction mismatches or invalid arguments are given.
    """
    try:
        # Evaluate with variables bound to full Quantity instances
        result = run_sandboxed(
            expression, 
            local_dict=parsed_subs, 
            globals_dict=PINT_CHECKING_NAMESPACE
        )
        if not isinstance(result, Quantity):
            # If standard primitive is returned, wrap it as dimensionless quantity
            result = ureg.Quantity(result)
        return result
    except DimensionalityError as e:
        raise UnitMismatchError(
            f"Dimensional inconsistency encountered: {e}",
            suggestion="Verify that added/compared variables have matching physical dimensions."
        )
    except UnitMismatchError as e:
        # Re-raise explicit unit mismatch errors directly
        raise e
    except Exception as e:
        # Fallback for unexpected validation issues during unit check phase
        raise UnitMismatchError(f"Failed to validate expression unit consistency: {e}")


def format_result(
    magnitude: Union[float, int, complex], 
    base_unit: Any, 
    output_unit_str: Optional[str] = None
) -> Dict[str, Any]:
    """
    Formats the raw calculated numeric result using Pint unit mappings.
    Explicitly enforces UTF-8 compatible plain-text formats to prevent Windows mojibakes.
    """
    # 1. Re-associate the magnitude with the evaluated base SI unit
    if isinstance(base_unit, Quantity):
        unit_obj = base_unit.units
    elif isinstance(base_unit, Unit):
        unit_obj = base_unit
    else:
        unit_obj = ureg.dimensionless

    base_quantity = ureg.Quantity(magnitude, unit_obj)

    # 2. Check if a specific target output unit is requested
    if output_unit_str:
        target_unit_str = output_unit_str.strip()
        try:
            formatted_quantity = base_quantity.to(target_unit_str)
        except (DimensionalityError, UndefinedUnitError) as e:
            raise UnitMismatchError(
                f"Cannot convert base units '{base_quantity.units}' to requested output units '{target_unit_str}': {e}",
                suggestion="Specify output units with matching dimensional metrics (e.g. converting Joule to kJ is valid)."
            )
    else:
        # Default to standard base unit reduction or base SI
        formatted_quantity = base_quantity.to_compact() if not base_quantity.dimensionless else base_quantity

    # 3. Format strings strictly in plain ASCII notation to guarantee safety against Windows encoding bugs
    # format "{:~}" gives plain ASCII units like "m / s ** 2", "kg * m / s ** 2"
    result_val = formatted_quantity.magnitude
    result_unit = f"{formatted_quantity.units:~}"
    result_pretty = f"{result_val} {result_unit}" if result_unit else f"{result_val}"
    
    # Generate exact Base SI format representation
    si_quantity = base_quantity.to_base_units()
    si_unit = f"{si_quantity.units:~}"
    result_si = f"{si_quantity.magnitude} {si_unit}" if si_unit else f"{si_quantity.magnitude}"

    return {
        "value": result_val,
        "unit": result_unit if result_unit else "dimensionless",
        "result_si": result_si,
        "result_pretty": result_pretty
    }
