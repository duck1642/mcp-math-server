# -*- coding: utf-8 -*-
"""
tools/plot.py - Sandboxed plotting tool.
Evaluates mathematical expressions safely and returns either self-contained matplotlib code
or a Base64-encoded PNG image for universal/direct client testing.
"""

from typing import Any, Dict, List, Optional, Union
import numpy as np
import sympy as sp
import io
import base64

# Enforce headless Matplotlib backend prior to import
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from core.errors import MathEvaluationError, format_error
from core.sandbox import run_sandboxed

def plot_tool(
    mode: str,
    expression: Optional[str] = None,
    x: Optional[List[Any]] = None,
    y: Optional[List[Any]] = None,
    variable: Optional[str] = None,
    range: Optional[List[float]] = None,
    title: Optional[str] = None,
    xlabel: Optional[str] = None,
    ylabel: Optional[str] = None,
    output_format: str = "code"
) -> Dict[str, Any]:
    """
    Evaluates plot data safely inside the AST sandbox.
    Can return self-contained matplotlib code ('code') or a Base64 PNG ('image').
    """
    try:
        plot_mode = mode.lower().strip()
        
        # 1. EVALUATE AND VALIDATE COORDINATE SERIES
        if plot_mode == "expression":
            if not expression:
                raise MathEvaluationError("Missing expression string for 'expression' plot mode.")
            if not variable:
                raise MathEvaluationError("Missing target independent variable for 'expression' plot mode.")
            if not range or len(range) < 2:
                raise MathEvaluationError("Missing or invalid plotting range. Supply a list containing [min, max].")
                
            # Parse limits and coordinate intervals
            lower_lim = float(range[0])
            upper_lim = float(range[1])
            points_count = int(range[2]) if len(range) > 2 else 150
            
            if lower_lim >= upper_lim:
                raise MathEvaluationError("Plotting range minimum must be strictly less than the maximum limit.")
                
            # Create linspace domain array
            x_vals = np.linspace(lower_lim, upper_lim, points_count)
            
            # Walk and compile mathematical function in AST sandbox (validation)
            var_sym = sp.Symbol(variable)
            ast_obj = run_sandboxed(expression, local_dict={variable: var_sym})
            sym_expr = sp.sympify(ast_obj)
            
            # Lambdify symbolic curve to vector-safe numpy callable
            compiled_curve = sp.lambdify(var_sym, sym_expr, modules=["numpy", "math"])
            
            try:
                y_raw = compiled_curve(x_vals)
            except Exception as e:
                raise MathEvaluationError(f"Failed to evaluate expression curve over the selected range: {e}")
                
            # Normalize vector returns (e.g. constant equations)
            if isinstance(y_raw, (int, float, complex)):
                y_vals = np.full_like(x_vals, y_raw, dtype=float)
            elif isinstance(y_raw, (list, tuple)):
                y_vals = np.array(y_raw, dtype=float)
            elif isinstance(y_raw, np.ndarray):
                y_vals = y_raw.astype(float)
            else:
                y_vals = np.array([float(val) for val in y_raw])
                
        elif plot_mode == "data":
            if x is None or y is None:
                raise MathEvaluationError("Missing coordinate array data. Supply both 'x' and 'y' lists.")
            if len(x) != len(y):
                raise MathEvaluationError(f"Coordinate size mismatch: x has size {len(x)} while y has size {len(y)}.")
            if len(x) == 0:
                raise MathEvaluationError("Coordinate arrays must contain at least one data point.")
                
            try:
                x_vals = np.array([float(val) for val in x])
                y_vals = np.array([float(val) for val in y])
            except (ValueError, TypeError) as e:
                raise MathEvaluationError(f"Failed to parse numerical arrays: {e}")
                
        else:
            raise MathEvaluationError(
                f"Unsupported plotting mode '{mode}'.",
                suggestion="Use 'expression' (for plotting mathematical functions) or 'data' (for plotting arrays)."
            )
            
        # 2. GENERATE AND FORMAT OUTPUT
        if output_format == "image":
            # Direct Image Generation
            fig, ax = plt.subplots(figsize=(7, 4.5))
            label = expression if expression else "Data Curve"
            
            plot_var = x_vals if (plot_mode == "expression" and variable) else x_vals
            ax.plot(plot_var, y_vals, color='#3b82f6', linewidth=2, label=label)
            
            if title:
                ax.set_title(title, fontsize=12, fontweight='bold')
            if xlabel:
                ax.set_xlabel(xlabel, fontsize=10)
            if ylabel:
                ax.set_ylabel(ylabel, fontsize=10)
                
            ax.grid(True, linestyle='--', alpha=0.5, color='#d1d5db')
            ax.legend()
            fig.tight_layout()
            
            img_buffer = io.BytesIO()
            try:
                fig.savefig(img_buffer, format="png", bbox_inches="tight")
                img_buffer.seek(0)
                img_base64 = base64.b64encode(img_buffer.getvalue()).decode("ascii")
                data_url = f"data:image/png;base64,{img_base64}"
                image_tag = f"![plot]({data_url})"
            finally:
                plt.close(fig)
                
            return {
                "status": "success",
                "mode": plot_mode,
                "data_url": data_url,
                "image_tag": image_tag
            }
            
        else:
            # Self-contained code output (default)
            label = expression if expression else "Data Curve"
            
            code_lines = [
                "import numpy as np",
                "from numpy import *",
                "import matplotlib.pyplot as plt",
                "E = e  # Euler's number alias",
                "",
            ]
            
            if plot_mode == "expression":
                code_lines.extend([
                    f"{variable} = np.linspace({lower_lim}, {upper_lim}, {points_count})",
                    f"y = {expression}",
                ])
            else:
                x_rounded = [round(v, 6) for v in x_vals.tolist()]
                y_rounded = [round(v, 6) for v in y_vals.tolist()]
                code_lines.extend([
                    f"x = {x_rounded}",
                    f"y = {y_rounded}",
                ])
            
            plot_var = variable if (plot_mode == "expression" and variable) else "x"
            
            code_lines.extend([
                "",
                "fig, ax = plt.subplots(figsize=(7, 4.5))",
                f"ax.plot({plot_var}, y, color='#3b82f6', linewidth=2, label={repr(label)})",
            ])
            
            if title:
                code_lines.append(f"ax.set_title({repr(title)}, fontsize=12, fontweight='bold')")
            if xlabel:
                code_lines.append(f"ax.set_xlabel({repr(xlabel)}, fontsize=10)")
            if ylabel:
                code_lines.append(f"ax.set_ylabel({repr(ylabel)}, fontsize=10)")
            
            code_lines.extend([
                "ax.grid(True, linestyle='--', alpha=0.5, color='#d1d5db')",
                "ax.legend()",
                "fig.tight_layout()",
                "plt.show()",
            ])
            
            code = "\n".join(code_lines)
            
            return {
                "status": "success",
                "mode": plot_mode,
                "code": code
            }
            
    except Exception as e:
        return format_error(e)
