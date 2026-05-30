# -*- coding: utf-8 -*-
"""
tests/test_solvers.py - Automated tests for symbolic and numerical solvers.
Verifies SymPy symbolic calculations and SciPy numerical solvers.
"""

import pytest
from tools.solve_symbolic import solve_symbolic_tool
from tools.solve_numeric import solve_numeric_tool

def test_symbolic_algebra_and_calculus():
    """Asserts that symbolic simplifies, integrals, derivations, and limits calculate correctly."""
    # Derivative of x**2 -> 2*x
    res_diff = solve_symbolic_tool("x**2", "diff", "x")
    assert res_diff["status"] == "success"
    assert res_diff["result_plain"] == "2*x"

    # Integration of 2*x -> x**2
    res_int = solve_symbolic_tool("2*x", "integrate", "x")
    assert res_int["status"] == "success"
    assert res_int["result_plain"] == "x**2"

    # Limit of sin(x)/x as x -> 0 is 1
    res_lim = solve_symbolic_tool("sin(x)/x", "limit", "x", extra={"point": 0})
    assert res_lim["status"] == "success"
    assert res_lim["result_plain"] == "1"

    # Expansion of (x + 1)**2 -> x**2 + 2*x + 1
    res_exp = solve_symbolic_tool("(x + 1)**2", "expand", "x")
    assert res_exp["status"] == "success"
    assert "2*x" in res_exp["result_plain"]


def test_symbolic_equation_solving():
    """Asserts that equations containing assignment operators solve correctly."""
    # x**2 - 4 = 0 -> solutions [-2, 2]
    res = solve_symbolic_tool("x**2 - 4 = 0", "solve", "x")
    assert res["status"] == "success"
    assert "-2" in res["result_plain"]
    assert "2" in res["result_plain"]


def test_numerical_root_finding():
    """Asserts that SciPy root finding computes exact solutions."""
    # Find root of x**2 - 9 = 0 with guess 4.0
    res = solve_numeric_tool("root", equations="x**2 - 9 = 0", variables="x", initial=[4.0])
    assert res["status"] == "success"
    assert abs(res["solutions"]["x"] - 3.0) < 1e-5


def test_numerical_minimization():
    """Asserts that minimization optimization converges onto expected points."""
    # Minimize (x - 2)**2, expecting minimum at x = 2.0
    res = solve_numeric_tool("minimize", expression="(x - 2)**2", variables="x", initial=[0.0])
    assert res["status"] == "success"
    assert abs(res["coordinates"]["x"] - 2.0) < 1e-5
    assert abs(res["minimum_value"]) < 1e-5


def test_numerical_definite_integration():
    """Asserts that definite numerical integration calculates exact area sizes."""
    # Integrate x**2 from 0 to 3 -> value is 9.0
    res = solve_numeric_tool("integrate", expression="x**2", variable="x", bounds=[0, 3])
    assert res["status"] == "success"
    assert abs(res["value"] - 9.0) < 1e-5


def test_dynamical_ode_systems():
    """Asserts that SciPy RK45 dynamical systems solver integrates vector systems."""
    # Solve dy/dt = -y from t=0 to t=2, y(0)=1
    # Analytical solution is y(t) = exp(-t) -> at t=2, y(2) = exp(-2) = 0.135335
    res = solve_numeric_tool(
        "ode", 
        equations="dy/dt = -y", 
        variables="y", 
        t_span=[0.0, 2.0], 
        initial=[1.0]
    )
    assert res["status"] == "success"
    t_points = res["t"]
    y_values = res["trajectories"]["y"]
    
    # Assert final trajectory value is exp(-2)
    assert abs(y_values[-1] - 0.135335) < 1e-3
