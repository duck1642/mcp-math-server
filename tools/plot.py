# -*- coding: utf-8 -*-
"""
tools/plot.py - Thread-safe in-memory Matplotlib plotting tool.
Renders analytical curves or numerical data arrays into SVGs, returning base64 markdown links.
"""

import io
import base64
from typing import Any, Dict, List, Optional, Union
import numpy as np
import sympy as sp

from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

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
    ylabel: Optional[str] = None
) -> Dict[str, Any]:
    """
    Renders high-quality graphical plots directly inside computer memory.
    Returns standard Base64-encoded SVG Data URLs formatted as inline Markdown images.
    """
    try:
        plot_mode = mode.lower().strip()
        
        # 1. EVALUATE COORDINATE SERIES
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
            
            # Walk and compile mathematical function in AST sandbox
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
            
        # 2. THREAD-SAFE OBJECT-ORIENTED DRAWING
        fig = Figure(figsize=(7, 4.5), dpi=100)
        canvas = FigureCanvas(fig)
        ax = fig.add_subplot(111)
        
        # Style layout using elegant dark theme markers
        ax.plot(x_vals, y_vals, color="#3b82f6", linewidth=2, label=expression if expression else "Data Curve")
        
        # Apply labels and titles
        if title:
            ax.set_title(title, fontsize=12, fontweight="bold", pad=12)
        if xlabel:
            ax.set_xlabel(xlabel, fontsize=10, labelpad=8)
        if ylabel:
            ax.set_ylabel(ylabel, fontsize=10, labelpad=8)
            
        ax.grid(True, linestyle="--", alpha=0.5, color="#d1d5db")
        ax.tick_params(colors="#4b5563")
        
        # Apply aesthetic boundary tweaks
        fig.tight_layout()
        
        # 3. WRITE TO IN-MEMORY STRING BUFFER & BASE64 ENCODE
        img_buffer = io.BytesIO()
        try:
            fig.savefig(img_buffer, format="svg", bbox_inches="tight")
            img_buffer.seek(0)
            # Encode explicitly to utf-8 safe base64
            b64_data = base64.b64encode(img_buffer.read()).decode("utf-8")
        finally:
            img_buffer.close()
            
        inline_markdown = f"![plot](data:image/svg+xml;base64,{b64_data})"
        
        return {
            "status": "success",
            "mode": plot_mode,
            "image_tag": inline_markdown,
            "data_url": f"data:image/svg+xml;base64,{b64_data}"
        }
        
    except Exception as e:
        return format_error(e)
