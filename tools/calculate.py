# -*- coding: utf-8 -*-
"""
tools/calculate.py - High-precision numerical expression evaluator tool.
Evaluates equations using a safe sandbox namespace with optional physical unit validation.
"""

from typing import Any, Dict, Optional
from core.errors import MathEvaluationError, format_error
from core.units import (
    parse_substitutions,
    validate_expression_units,
    format_result,
    parse_quantity
)
from core.sandbox import run_sandboxed
from core.namespace import ureg

def calculate_tool(
    expression: str,
    substitutions: Optional[Dict[str, Any]] = None,
    use_units: bool = False,
    output_unit: Optional[str] = None
) -> Dict[str, Any]:
    """
    Evaluates a sandboxed numerical expression using numpy, scipy, cmath, or math.
    Supports physical unit parsing, dimension verification, and SI conversions.
    """
    try:
        # 1. Handle unit-aware calculation pathway
        if use_units:
            # Parse input substitution values into Pint Quantities
            parsed_subs = parse_substitutions(substitutions)
            
            # Step A: Perform dimensional checking phase (throws on dimension mismatch)
            checked_output = validate_expression_units(expression, parsed_subs)
            
            # Step B: Convert variable quantities to base SI and extract dimensionless magnitudes
            eval_locals = {}
            for var, qty in parsed_subs.items():
                eval_locals[var] = qty.to_base_units().magnitude
                
            # Step C: Evaluate expression using the dimensionless magnitudes in the sandbox
            numeric_res = run_sandboxed(expression, local_dict=eval_locals)
            
            # Step D: Apply inferred SI units to numeric result and format output
            formatted = format_result(numeric_res, checked_output, output_unit)
            
            return {
                "status": "success",
                "value": formatted["value"],
                "unit": formatted["unit"],
                "result_si": formatted["result_si"],
                "result_pretty": formatted["result_pretty"],
                "units_verified": True
            }
            
        # 2. Handle unitless standard calculation pathway
        else:
            eval_locals = {}
            if substitutions:
                for var, val in substitutions.items():
                    # Parse values to floats/numbers (dropping units if present)
                    if isinstance(val, (int, float, complex)):
                        eval_locals[var] = val
                    else:
                        try:
                            # Parse using Pint and extract magnitude
                            qty = parse_quantity(val)
                            eval_locals[var] = qty.magnitude
                        except Exception:
                            # Fallback if standard float parsing is needed
                            eval_locals[var] = float(val)
                            
            numeric_res = run_sandboxed(expression, local_dict=eval_locals)
            
            # Format outputs as dimensionless primitives
            return {
                "status": "success",
                "value": numeric_res,
                "unit": "dimensionless",
                "result_si": str(numeric_res),
                "result_pretty": str(numeric_res),
                "units_verified": False
            }
            
    except Exception as e:
        # Catch and serialize predictable or system-level mathematical errors
        return format_error(e)
