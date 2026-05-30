# -*- coding: utf-8 -*-
"""
tools/solve_symbolic.py - Symbolic calculation and algebra solver tool.
Integrates SymPy for derivatives, integrations, simplification, expansion, and limits.
"""

import ast
from typing import Any, Dict, Optional, Set, Union
import sympy as sp

from core.errors import MathEvaluationError, format_error
from core.sandbox import run_sandboxed
from core.namespace import SCIENCE_NAMESPACE

def extract_variables(expr_str: str) -> Set[str]:
    """
    Parses a string expression into an AST tree and extracts all user-defined variable names.
    Ignores preloaded scientific packages and standard whitelisted functions.
    """
    clean = expr_str.strip()
    if not clean:
        return set()
        
    # Replace single assignment with double to allow AST parsing for variable extraction
    parse_target = clean.replace("=", "==") if "=" in clean and "==" not in clean else clean
    
    try:
        tree = ast.parse(parse_target, mode="eval")
    except Exception:
        # Fallback split approach if AST parsing fails on assignments
        if "=" in clean:
            parts = clean.split("=")
            vars_found = set()
            for p in parts:
                p_clean = p.strip()
                if p_clean and p_clean != clean:
                    vars_found.update(extract_variables(p_clean))
            return vars_found
        return set()
        
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            name_id = node.id
            # Filter out standard keywords and scientific library names
            if name_id not in SCIENCE_NAMESPACE and not name_id.startswith("_"):
                names.add(name_id)
    return names


def solve_symbolic_tool(
    expression: str,
    operation: str,
    variable: str,
    domain: str = "complex",
    extra: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Exposes SymPy capabilities inside the secure AST execution sandbox.
    Handles equation pre-processing, domain specification, and latex output parsing.
    """
    try:
        if not variable or not variable.strip():
            raise MathEvaluationError(
                "Variable name cannot be empty.",
                suggestion="Provide a valid non-empty variable name (e.g., 'x', 'n')."
            )

        # 1. Parse equations containing a single "=" assignment operator
        clean_expr = expression.strip()
        has_equals = "=" in clean_expr and "==" not in clean_expr
        
        lhs_str = clean_expr
        rhs_str = "0"
        
        if has_equals:
            parts = clean_expr.split("=")
            if len(parts) != 2:
                raise MathEvaluationError(
                    "Invalid equation format. Equations must contain exactly one '=' operator."
                )
            lhs_str, rhs_str = parts[0].strip(), parts[1].strip()
            
        # 2. Extract and define mathematical symbols dynamically
        variables_found = extract_variables(lhs_str) | extract_variables(rhs_str)
        variables_found.add(variable)
        
        is_real = (domain.lower() == "real")
        syms_dict = {}
        for var_name in variables_found:
            # Create typed symbols inside local scope without inconsistent assumptions
            if is_real:
                syms_dict[var_name] = sp.Symbol(var_name, real=True)
            else:
                syms_dict[var_name] = sp.Symbol(var_name, complex=True)
            
        # 3. Evaluate expression LHS and RHS inside AST sandbox
        lhs_eval = run_sandboxed(lhs_str, local_dict=syms_dict)
        rhs_eval = run_sandboxed(rhs_str, local_dict=syms_dict)
        
        # Ensure we have SymPy objects
        lhs_sym = sp.sympify(lhs_eval)
        rhs_sym = sp.sympify(rhs_eval)
        
        target_var_sym = syms_dict[variable]
        
        # 4. Perform the requested SymPy operation
        op = operation.lower().strip()
        
        if op == "solve":
            # Solve equality relation Eq(lhs, rhs)
            eq_relation = sp.Eq(lhs_sym, rhs_sym)
            res = sp.solve(eq_relation, target_var_sym)
            
        elif op == "simplify":
            res = sp.simplify(lhs_sym)
            
        elif op == "expand":
            res = sp.expand(lhs_sym)
            
        elif op == "diff":
            # Optional extra order attribute (e.g. 2nd derivative)
            order = int(extra.get("order", 1)) if extra else 1
            res = sp.diff(lhs_sym, target_var_sym, order)
            
        elif op == "integrate":
            # Support definite integration if bounds are supplied in extra
            bounds = extra.get("bounds", None) if extra else None
            if bounds:
                # bounds should be a list/tuple like [lower, upper]
                if not isinstance(bounds, (list, tuple)) or len(bounds) != 2:
                    raise MathEvaluationError("Definite integral bounds must be a list containing [lower, upper].")
                lower = sp.sympify(bounds[0])
                upper = sp.sympify(bounds[1])
                res = sp.integrate(lhs_sym, (target_var_sym, lower, upper))
            else:
                res = sp.integrate(lhs_sym, target_var_sym)
                
        elif op == "limit":
            point = extra.get("point", 0) if extra else 0
            point_sym = sp.sympify(point)
            direction = extra.get("dir", "+") if extra else "+"
            res = sp.limit(lhs_sym, target_var_sym, point_sym, dir=direction)
            
        elif op == "series":
            point = extra.get("point", 0) if extra else 0
            order = int(extra.get("order", 6)) if extra else 6
            point_sym = sp.sympify(point)
            res = sp.series(lhs_sym, target_var_sym, point_sym, order)
            
        elif op == "summation":
            bounds = extra.get("bounds", None) if extra else None
            if not bounds or not isinstance(bounds, (list, tuple)) or len(bounds) != 2:
                raise MathEvaluationError("Summation bounds must be a list containing [lower, upper].")
            lower = sp.sympify(bounds[0])
            upper = sp.sympify(bounds[1])
            res = sp.summation(lhs_sym, (target_var_sym, lower, upper))
            try:
                res = sp.simplify(res)
            except Exception:
                pass
            
        elif op == "product":
            bounds = extra.get("bounds", None) if extra else None
            if not bounds or not isinstance(bounds, (list, tuple)) or len(bounds) != 2:
                raise MathEvaluationError("Product bounds must be a list containing [lower, upper].")
            lower = sp.sympify(bounds[0])
            upper = sp.sympify(bounds[1])
            
            if upper == sp.oo:
                try:
                    # Evaluate infinite product as the limit of a finite product
                    _k = sp.Symbol("_k", integer=True, positive=True)
                    res_finite = sp.product(lhs_sym, (target_var_sym, lower, _k))
                    res_simp = sp.simplify(res_finite)
                    res = sp.limit(res_simp, _k, sp.oo)
                except Exception:
                    res = sp.product(lhs_sym, (target_var_sym, lower, upper))
            else:
                res = sp.product(lhs_sym, (target_var_sym, lower, upper))
                try:
                    res = sp.simplify(res)
                except Exception:
                    pass
            
        elif op == "sequence_limit":
            res = sp.limit(lhs_sym, target_var_sym, sp.oo)
            
        elif op == "convergence":
            bounds = extra.get("bounds", None) if extra else None
            if bounds and isinstance(bounds, (list, tuple)) and len(bounds) == 2:
                lower = sp.sympify(bounds[0])
                upper = sp.sympify(bounds[1])
                sum_obj = sp.Sum(lhs_sym, (target_var_sym, lower, upper))
                res = sum_obj.is_convergent()
            else:
                sum_obj = sp.Sum(lhs_sym, (target_var_sym, 1, sp.oo))
                res = sum_obj.is_convergent()
            
        else:
            raise MathEvaluationError(
                f"Unsupported symbolic operation '{operation}'.",
                suggestion="Use one of the whitelisted operations: 'solve', 'simplify', 'expand', 'diff', 'integrate', 'limit', 'series', 'summation', 'product', 'sequence_limit', 'convergence'."
            )
            
        # 5. Format and serialize output
        # Handle list-based solution outputs (e.g. roots)
        if isinstance(res, (list, tuple)):
            result_plain = [str(item) for item in res]
            result_latex = [sp.latex(item) for item in res]
            is_list = True
        elif isinstance(res, dict):
            # If system solve returns dict
            result_plain = {str(k): str(v) for k, v in res.items()}
            result_latex = {sp.latex(k): sp.latex(v) for k, v in res.items()}
            is_list = False
        else:
            result_plain = str(res)
            result_latex = sp.latex(res)
            is_list = False
            
        return {
            "status": "success",
            "operation": op,
            "variable": variable,
            "domain": domain,
            "is_list": is_list,
            "result_plain": result_plain,
            "result_latex": result_latex
        }
        
    except Exception as e:
        return format_error(e)
