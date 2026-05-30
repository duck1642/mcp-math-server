# -*- coding: utf-8 -*-
"""
tools/solve_numeric.py - High-precision numerical solvers tool.
Provides root-finding, optimization, definite integration, and ODE integration using SciPy.
"""

from typing import Any, Dict, List, Optional, Union
import numpy as np
import scipy.optimize
import scipy.integrate
import sympy as sp

from core.errors import MathEvaluationError, format_error, DivergentIntegralError
from core.sandbox import run_sandboxed
from core.units import parse_substitutions, parse_quantity, ureg

def solve_numeric_tool(
    method: str,
    expression: Optional[Union[str, List[str]]] = None,
    equations: Optional[Union[str, List[str]]] = None,
    variable: Optional[Union[str, List[str]]] = None,
    variables: Optional[Union[str, List[str]]] = None,
    bounds: Optional[List[Any]] = None,
    t_span: Optional[List[float]] = None,
    initial: Optional[List[float]] = None,
    substitutions: Optional[Dict[str, Any]] = None,
    use_units: bool = False
) -> Dict[str, Any]:
    """
    Solves numerical equations, optimizations, integrals, and ODE systems.
    Utilizes scipy.optimize and scipy.integrate behind an AST sandboxed compiler.
    """
    try:
        # Normalize input targets and systems
        target_exprs = expression or equations
        if not target_exprs:
            raise MathEvaluationError("Missing calculation targets. Please supply 'expression' or 'equations'.")
            
        target_vars = variable or variables
        if not target_vars:
            raise MathEvaluationError("Missing target variables. Please supply 'variable' or 'variables'.")
            
        # Standardize strings to lists
        expr_list = [target_exprs] if isinstance(target_exprs, str) else list(target_exprs)
        var_list = [target_vars] if isinstance(target_vars, str) else list(target_vars)
        
        method_name = method.lower().strip()
        
        # 1. ROOT FINDING METHOD
        if method_name == "root":
            # Initial guess defaults to 1.0 for each target variable
            init_guess = list(initial) if initial else [1.0] * len(var_list)
            if len(init_guess) != len(var_list):
                raise MathEvaluationError(
                    f"Initial guess count ({len(init_guess)}) does not match variable count ({len(var_list)})."
                )
                
            # Process assignment equations (LHS = RHS -> LHS - RHS)
            sym_exprs = []
            for eq in expr_list:
                clean_eq = eq.strip()
                if "=" in clean_eq and "==" not in clean_eq:
                    parts = clean_eq.split("=")
                    sym_exprs.append(f"({parts[0]}) - ({parts[1]})")
                else:
                    sym_exprs.append(clean_eq)
                    
            # Parse symbolic representations inside the AST sandbox
            var_syms = [sp.Symbol(v) for v in var_list]
            subs_parsed = {}
            if substitutions:
                for k, v in substitutions.items():
                    # Parse using Pint if use_units is requested, else extract magnitude
                    qty = parse_quantity(v)
                    subs_parsed[k] = qty.to_base_units().magnitude if use_units else qty.magnitude
                    
            # Build local binding symbols
            local_dict = {v: sp.Symbol(v) for v in var_list}
            local_dict.update({k: sp.Symbol(k) for k in subs_parsed})
            
            ast_exprs = []
            for se in sym_exprs:
                ast_exprs.append(run_sandboxed(se, local_dict=local_dict))
                
            # Perform substitutions on symbolic expressions
            substituted_syms = [sp.sympify(ae).subs(subs_parsed) for ae in ast_exprs]
            
            # Lambdify the symbolic system
            compiled_sys = sp.lambdify(var_syms, substituted_syms, modules=["numpy", "math"])
            
            # Wrap system to handle numpy vectors safely
            def root_func(x):
                # Ensure x is unpacked if list/array
                val = compiled_sys(*x)
                # scipy.optimize.root expects a flat sequence/list return
                return list(val) if isinstance(val, (list, tuple, np.ndarray)) else [val]
                
            # Solve using Scipy root optimization solver
            res = scipy.optimize.root(root_func, init_guess)
            
            if not res.success:
                raise MathEvaluationError(f"Root finder failed to converge: {res.message}")
                
            # Associate output values to respective units if requested
            result_values = res.x.tolist()
            result_map = {}
            for v, val in zip(var_list, result_values):
                result_map[v] = val
                
            return {
                "status": "success",
                "method": "root",
                "converged": bool(res.success),
                "solutions": result_map,
                "message": res.message
            }
            
        # 2. MINIMIZE METHOD
        elif method_name == "minimize":
            init_guess = list(initial) if initial else [1.0] * len(var_list)
            if len(init_guess) != len(var_list):
                raise MathEvaluationError(
                    f"Initial guess count ({len(init_guess)}) does not match variable count ({len(var_list)})."
                )
                
            # Minimize expects a single objective scalar expression
            if len(expr_list) != 1:
                raise MathEvaluationError("Minimize objective function must be a single scalar expression.")
                
            # Parse objective expression in AST sandbox
            var_syms = [sp.Symbol(v) for v in var_list]
            subs_parsed = {}
            if substitutions:
                for k, v in substitutions.items():
                    qty = parse_quantity(v)
                    subs_parsed[k] = qty.to_base_units().magnitude if use_units else qty.magnitude
                    
            local_dict = {v: sp.Symbol(v) for v in var_list}
            local_dict.update({k: sp.Symbol(k) for k in subs_parsed})
            
            ast_obj = run_sandboxed(expr_list[0], local_dict=local_dict)
            substituted_sym = sp.sympify(ast_obj).subs(subs_parsed)
            
            # Compile using SymPy lambdify
            compiled_obj = sp.lambdify(var_syms, substituted_sym, modules=["numpy", "math"])
            
            def obj_func(x):
                return float(compiled_obj(*x))
                
            # Handle bounds parameters
            scipy_bounds = None
            if bounds:
                # bounds should be a list of lists/tuples, e.g. [[xmin, xmax], [ymin, ymax]]
                scipy_bounds = []
                for b in bounds:
                    if b is None:
                        scipy_bounds.append((None, None))
                    elif isinstance(b, (list, tuple)) and len(b) == 2:
                        scipy_bounds.append((b[0], b[1]))
                    else:
                        raise MathEvaluationError("Bounds entries must be lists/tuples containing [min, max] or None.")
                        
            res = scipy.optimize.minimize(obj_func, init_guess, bounds=scipy_bounds)
            
            if not res.success:
                raise MathEvaluationError(f"Optimization minimizer failed to converge: {res.message}")
                
            result_map = {v: val for v, val in zip(var_list, res.x.tolist())}
            
            return {
                "status": "success",
                "method": "minimize",
                "converged": bool(res.success),
                "minimum_value": float(res.fun),
                "coordinates": result_map,
                "message": res.message
            }
            
        # 3. DEFINITE INTEGRATION METHOD
        elif method_name == "integrate":
            if len(expr_list) != 1 or len(var_list) != 1:
                raise MathEvaluationError("Integrate method requires exactly 1 expression and 1 target variable.")
                
            if not bounds or len(bounds) != 2:
                raise MathEvaluationError("Integration bounds must be a list containing [lower, upper].")
                
            # Perform AST sandbox checking
            var_sym = sp.Symbol(var_list[0])
            subs_parsed = {}
            if substitutions:
                for k, v in substitutions.items():
                    qty = parse_quantity(v)
                    subs_parsed[k] = qty.to_base_units().magnitude if use_units else qty.magnitude
                    
            local_dict = {var_list[0]: var_sym}
            local_dict.update({k: sp.Symbol(k) for k in subs_parsed})
            
            ast_obj = run_sandboxed(expr_list[0], local_dict=local_dict)
            substituted_sym = sp.sympify(ast_obj).subs(subs_parsed)
            
            # Try symbolic definite integration first to resolve improper integrals exactly
            val = None
            err = 0.0
            convergent = True
            
            # Helper to map string infinity bounds to actual SymPy infinity objects
            def parse_sp_bound(b):
                if isinstance(b, str):
                    clean_b = b.strip().lower()
                    if clean_b in ("inf", "+inf", "oo", "+oo"):
                        return sp.oo
                    if clean_b in ("-inf", "-oo"):
                        return -sp.oo
                return sp.sympify(b)
                
            try:
                # Convert bounds to SymPy expressions
                sp_lower = parse_sp_bound(bounds[0])
                sp_upper = parse_sp_bound(bounds[1])
                
                sym_res = sp.integrate(substituted_sym, (var_sym, sp_lower, sp_upper))
                
                # Check for explicit divergence
                if sym_res == sp.oo or sym_res == -sp.oo or sym_res.has(sp.oo) or sym_res.has(-sp.oo):
                    raise DivergentIntegralError("Improper integral diverges.")
                    
                if sym_res.is_number and not isinstance(sym_res, sp.Integral):
                    val = float(sym_res)
                    err = 0.0
                    convergent = True
            except DivergentIntegralError as die:
                raise die
            except Exception:
                # Fallback to numerical integration if symbolic integration is not available
                val = None
                
            if val is None:
                import warnings
                from scipy.integrate import IntegrationWarning
                
                # Map standard string oo/inf names to float infinity for SciPy
                def parse_bound(b):
                    if isinstance(b, str):
                        clean_b = b.strip().lower()
                        if clean_b in ("oo", "inf", "+oo", "+inf"):
                            return float("inf")
                        if clean_b in ("-oo", "-inf"):
                            return float("-inf")
                    return float(b)
                    
                lower_f = parse_bound(bounds[0])
                upper_f = parse_bound(bounds[1])
                
                compiled_integrand = sp.lambdify(var_sym, substituted_sym, modules=["numpy", "math"])
                
                with warnings.catch_warnings(record=True) as caught_warnings:
                    warnings.simplefilter("always", IntegrationWarning)
                    try:
                        val, err = scipy.integrate.quad(compiled_integrand, lower_f, upper_f)
                    except Exception as e:
                        raise DivergentIntegralError(f"Numerical integration failed: {e}")
                        
                # Check for SciPy divergence warning triggers
                if caught_warnings:
                    warn_msg = str(caught_warnings[0].message)
                    raise DivergentIntegralError(
                        f"Numerical integration failed to converge: {warn_msg}",
                        suggestion="Check if the integral diverges mathematically or has interior singularities."
                    )
                    
                # Classify convergence based on estimated relative error bounds
                if val != 0:
                    rel_err = abs(err / val)
                    if rel_err > 1e-2 and abs(err) > 1e-3:
                        raise DivergentIntegralError(
                            f"Numerical integration failed to converge. Estimated absolute error: {err}, relative error: {rel_err:.4f}",
                            suggestion="Check for slow convergence or potential mathematical divergence."
                        )
                elif abs(err) > 1e-3:
                    raise DivergentIntegralError(
                        f"Numerical integration failed to converge. Result is zero but estimated absolute error is unacceptably high ({err}).",
                        suggestion="Check if the integral converges mathematically."
                    )
                    
                convergent = True

            return {
                "status": "success",
                "method": "integrate",
                "value": val,
                "absolute_error": err,
                "convergent": convergent,
                "bounds": bounds
            }
            
        # 4. ODE DYNAMICAL SYSTEMS SOLVER
        elif method_name == "ode":
            if not t_span or len(t_span) != 2:
                raise MathEvaluationError("ODE t_span must be a list/tuple containing [t0, tf].")
                
            if not initial or len(initial) != len(var_list):
                raise MathEvaluationError(
                    f"ODE initial conditions count ({len(initial if initial else [])}) "
                    f"must match dependent variables count ({len(var_list)})."
                )
                
            # Standard independent variable symbol defaults to 't'
            t_sym = sp.Symbol("t")
            var_syms = [sp.Symbol(v) for v in var_list]
            
            subs_parsed = {}
            if substitutions:
                for k, v in substitutions.items():
                    qty = parse_quantity(v)
                    subs_parsed[k] = qty.to_base_units().magnitude if use_units else qty.magnitude
                    
            local_dict = {"t": t_sym}
            local_dict.update({v: sp.Symbol(v) for v in var_list})
            local_dict.update({k: sp.Symbol(k) for k in subs_parsed})
            
            # Compile each ODE derivative expression inside sandbox
            ast_eqs = []
            for eq in expr_list:
                # Remove left side assignment of dy/dt if written e.g. "dy/dt = y" -> "y"
                clean_eq = eq.strip()
                if "=" in clean_eq and "==" not in clean_eq:
                    clean_eq = clean_eq.split("=")[1].strip()
                ast_eqs.append(run_sandboxed(clean_eq, local_dict=local_dict))
                
            substituted_eqs = [sp.sympify(ae).subs(subs_parsed) for ae in ast_eqs]
            
            # Lambdify dy/dt = f(t, [y1, y2])
            compiled_derivs = sp.lambdify((t_sym, var_syms), substituted_eqs, modules=["numpy", "math"])
            
            def ode_func(t, y):
                # scipy solver passes y as a numpy array. Unpack inside lambdified callable.
                derivs = compiled_derivs(t, y)
                # scipy.integrate.solve_ivp expects a list/array return
                return derivs if isinstance(derivs, (list, tuple, np.ndarray)) else [derivs]
                
            res = scipy.integrate.solve_ivp(ode_func, t_span, initial, method="RK45")
            
            if not res.success:
                raise MathEvaluationError(f"ODE integration failed: {res.message}")
                
            # Return time coordinate points and corresponding dependent trajectories
            trajectories = {}
            for v, values in zip(var_list, res.y.tolist()):
                trajectories[v] = values
                
            return {
                "status": "success",
                "method": "ode",
                "converged": bool(res.success),
                "t": res.t.tolist(),
                "trajectories": trajectories,
                "message": res.message
            }
            
        else:
            raise MathEvaluationError(
                f"Unsupported numerical method '{method}'.",
                suggestion="Use one of the whitelisted methods: 'root', 'minimize', 'integrate', 'ode'."
            )
            
    except Exception as e:
        return format_error(e)
