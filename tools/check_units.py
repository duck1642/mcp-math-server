# -*- coding: utf-8 -*-
"""
tools/check_units.py - Explicit diagnostic tool for dimensional analysis.
Exposes dimensional reduction, unit compatibility assertion, and SI reduction formulas.
"""

from typing import Any, Dict, Optional
from core.errors import format_error, UnitMismatchError
from core.units import parse_substitutions, validate_expression_units
from core.namespace import ureg

def check_units_tool(
    quantities: Dict[str, Any],
    check: Optional[str] = None,
    expression: Optional[str] = None
) -> Dict[str, Any]:
    """
    Diagnostic tool for checking physical variable dimensions, verifying equation consistency,
    and outputting clear dimensional formulas.
    """
    try:
        # 1. Parse incoming quantities into Pint Quantity representations
        parsed_subs = parse_substitutions(quantities)
        
        # Build individual summary of each parsed variable
        variables_summary = {}
        for var, qty in parsed_subs.items():
            variables_summary[var] = {
                "units": f"{qty.units:~}",
                "dimensions": str(qty.dimensionality),
                "base_units": f"{qty.to_base_units().units:~}",
                "magnitude_si": qty.to_base_units().magnitude
            }
            
        # 2. Handle compatibility checks across all provided quantities
        compatibility_status = "not_evaluated"
        compatibility_report = ""
        
        if check == "compatibility":
            if not parsed_subs:
                compatibility_status = "empty"
                compatibility_report = "No quantities supplied for compatibility check."
            else:
                # Retrieve first item to compare others against
                first_var, first_qty = next(iter(parsed_subs.items()))
                first_dim = first_qty.dimensionality
                
                mismatches = []
                for var, qty in parsed_subs.items():
                    if qty.dimensionality != first_dim:
                        mismatches.append(
                            f"Variable '{var}' has dimensions {qty.dimensionality} ({qty.units}), "
                            f"which is incompatible with '{first_var}' ({first_qty.units})."
                        )
                        
                if mismatches:
                    compatibility_status = "incompatible"
                    compatibility_report = "Dimensional mismatches found: " + "; ".join(mismatches)
                else:
                    compatibility_status = "compatible"
                    compatibility_report = (
                        f"All supplied quantities are physically compatible. "
                        f"Shared dimensions: {first_dim}."
                    )
                    
        # 3. Handle explicit expression dimensional analysis
        expression_summary = {}
        if expression:
            # Perform dimensional tracking inside checker sandbox
            checked_qty = validate_expression_units(expression, parsed_subs)
            expression_summary = {
                "expression": expression,
                "inferred_units": f"{checked_qty.units:~}",
                "dimensions": str(checked_qty.dimensionality),
                "base_si_units": f"{checked_qty.to_base_units().units:~}"
            }
            
        return {
            "status": "success",
            "variables": variables_summary,
            "compatibility_check": {
                "status": compatibility_status,
                "report": compatibility_report
            } if check == "compatibility" else None,
            "expression_analysis": expression_summary if expression else None
        }
        
    except Exception as e:
        return format_error(e)
