# -*- coding: utf-8 -*-
"""
server.py - MCP Math Server Entry Point.
Initializes FastMCP application and registers sandboxed math computational tools.
"""

import json
import base64
from typing import Any, Dict, List, Optional, Union
from mcp.server.fastmcp import FastMCP, Image

# Import underlying computational engines
from tools.calculate import calculate_tool
from tools.solve_symbolic import solve_symbolic_tool
from tools.solve_numeric import solve_numeric_tool
from tools.check_units import check_units_tool
from tools.plot import plot_tool
from core.serialization import clean_object

# Initialize the FastMCP Math Server
mcp = FastMCP("mcp-math-server")

@mcp.tool()
def calculate(
    expression: str,
    substitutions: Optional[Dict[str, Any]] = None,
    use_units: bool = False,
    output_unit: Optional[str] = None
) -> str:
    """
    Evaluates a numerical expression inside a safe sandbox with optional physical unit validation.
    
    Args:
        expression: Numerical equation string to compute (e.g. 'F * L' or 'np.sin(x)').
        substitutions: Map of variables to physical values/units (e.g. {'F': '500 N', 'L': '2 m'}).
        use_units: Set True to enable Pint unit verification and dimensional consistency checking.
        output_unit: Target physical unit for conversion of the result (e.g. 'kJ' or 'mm').
    """
    res = calculate_tool(
        expression=expression,
        substitutions=substitutions,
        use_units=use_units,
        output_unit=output_unit
    )
    # Enforce utf-8 compliance and prevent mojibakes
    return json.dumps(clean_object(res), indent=2, ensure_ascii=False)


@mcp.tool()
def solve_symbolic(
    expression: str,
    operation: str,
    variable: str,
    domain: str = "complex",
    extra: Optional[Dict[str, Any]] = None
) -> str:
    """
    Performs symbolic algebra, derivatives, integrations, simplifications, and limits using SymPy.
    
    Args:
        expression: Algebraic equation or expression string to analyze (e.g. 'x**2 - 4 = 0' or 'x*sin(x)').
        operation: Symbolic algorithm to run ('solve', 'simplify', 'expand', 'diff', 'integrate', 'limit').
        variable: Target dependent symbol variable name (e.g. 'x').
        domain: Mathematical domain assumption mapping ('real' or 'complex').
        extra: Parameters such as {'order': 2} for derivatives or {'bounds': [0, 1]} for definite integrals.
    """
    res = solve_symbolic_tool(
        expression=expression,
        operation=operation,
        variable=variable,
        domain=domain,
        extra=extra
    )
    return json.dumps(clean_object(res), indent=2, ensure_ascii=False)


@mcp.tool()
def solve_numeric(
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
) -> str:
    """
    High-precision numerical equation solvers, optimizations, integrations, and ODE solvers via SciPy.
    
    Args:
        method: Solver routine ('root', 'minimize', 'integrate', 'ode').
        expression: Objective mathematical expression string (required for minimize/integrate).
        equations: Equation or system list of equations (required for root/ode, e.g. ['x + y = 3', 'x - y = 1']).
        variable: Target variable name string (required for integrate).
        variables: Target variables name list/string (required for root/minimize/ode).
        bounds: Variable range search boundaries (e.g. [[0, 10], [0, 10]] or integration range [lower, upper]).
        t_span: Integration time boundaries for dynamical ODE solvers, list like [t0, tf].
        initial: Target initial conditions guess coordinate vector.
        substitutions: Constant mapping variables to physical values/units.
        use_units: Set True to apply physical unit conversions.
    """
    res = solve_numeric_tool(
        method=method,
        expression=expression,
        equations=equations,
        variable=variable,
        variables=variables,
        bounds=bounds,
        t_span=t_span,
        initial=initial,
        substitutions=substitutions,
        use_units=use_units
    )
    return json.dumps(clean_object(res), indent=2, ensure_ascii=False)


@mcp.tool()
def check_units(
    quantities: Dict[str, Any],
    check: Optional[str] = None,
    expression: Optional[str] = None
) -> str:
    """
    Explicit diagnostic tool for physical unit dimensional analysis and compatibility reporting.
    
    Args:
        quantities: Dict mapping physical variable names to physical value strings (e.g. {'E': '200 GPa', 'I': '8.33e-6 m^4'}).
        check: Set 'compatibility' to verify variables can be added/subtracted safely together.
        expression: Optional equation string to resolve and extract base SI dimensional metrics.
    """
    res = check_units_tool(
        quantities=quantities,
        check=check,
        expression=expression
    )
    return json.dumps(clean_object(res), indent=2, ensure_ascii=False)


@mcp.tool()
def plot(
    mode: str,
    expression: Optional[str] = None,
    x: Optional[List[Any]] = None,
    y: Optional[List[Any]] = None,
    variable: Optional[str] = None,
    range: Optional[List[float]] = None,
    title: Optional[str] = None,
    xlabel: Optional[str] = None,
    ylabel: Optional[str] = None
) -> str:
    """
    Evaluates a mathematical expression inside the sandbox and returns self-contained matplotlib code for rendering.
    
    Args:
        mode: Plotting source ('expression' for analytic formulas, 'data' for coordinate arrays).
        expression: Analytical curve equation string to compute (e.g. 'sin(x)').
        x: X-coordinate numerical data list (required for 'data' mode).
        y: Y-coordinate numerical data list (required for 'data' mode).
        variable: Independent curve coordinate symbol string (required for 'expression' mode).
        range: Bound interval range [min, max] or [min, max, points] (required for 'expression' mode).
        title: Optional title label for the graphic.
        xlabel: Optional X-axis coordinate label.
        ylabel: Optional Y-axis coordinate label.
    """
    res = plot_tool(
        mode=mode,
        expression=expression,
        x=x,
        y=y,
        variable=variable,
        range=range,
        title=title,
        xlabel=xlabel,
        ylabel=ylabel,
        output_format="code"
    )
    return json.dumps(clean_object(res), indent=2, ensure_ascii=False)


@mcp.tool()
def plot_image(
    mode: str,
    expression: Optional[str] = None,
    x: Optional[List[Any]] = None,
    y: Optional[List[Any]] = None,
    variable: Optional[str] = None,
    range: Optional[List[float]] = None,
    title: Optional[str] = None,
    xlabel: Optional[str] = None,
    ylabel: Optional[str] = None
) -> Image:
    """
    [EXPERIMENT/TEST FEATURE] Generates dynamic graphic curves or coordinate arrays in memory, returning an MCP Image object.
    
    Args:
        mode: Plotting source ('expression' for analytic formulas, 'data' for coordinate arrays).
        expression: Analytical curve equation string to compute (e.g. 'sin(x)').
        x: X-coordinate numerical data list (required for 'data' mode).
        y: Y-coordinate numerical data list (required for 'data' mode).
        variable: Independent curve coordinate symbol string (required for 'expression' mode).
        range: Bound interval range [min, max] or [min, max, points] (required for 'expression' mode).
        title: Optional title label for the graphic.
        xlabel: Optional X-axis coordinate label.
        ylabel: Optional Y-axis coordinate label.
    """
    res = plot_tool(
        mode=mode,
        expression=expression,
        x=x,
        y=y,
        variable=variable,
        range=range,
        title=title,
        xlabel=xlabel,
        ylabel=ylabel,
        output_format="image"
    )
    
    if res["status"] == "error":
        raise ValueError(res.get("message", "An error occurred during plot image generation."))
        
    b64_data = res["data_url"].split(",")[1]
    png_bytes = base64.b64decode(b64_data)
    
    return Image(data=png_bytes, format="png")


if __name__ == "__main__":
    import os
    import sys
    from mcp.server.transport_security import TransportSecuritySettings
    
    # Launch in SSE mode if --http, --sse, or HTTP_PORT is specified
    if "--http" in sys.argv or "--sse" in sys.argv or "HTTP_PORT" in os.environ:
        port = int(os.environ.get("HTTP_PORT", 8080))
        # Update settings port dynamically for FastMCP
        mcp.settings.port = port
        # Disable DNS rebinding protection for public tunneling compatibility
        mcp.settings.transport_security = TransportSecuritySettings(
            enable_dns_rebinding_protection=False
        )
        # Use sse transport for network compatibility
        mcp.run(transport="sse")
    else:
        # Default to standard stdio for local clients
        mcp.run()
