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
    assert res["convergent"] is True


def test_definite_integration_convergence_regression():
    """Asserts definite integration convergence/divergence behaves correctly on improper integrals."""
    # 1. ∫₁^∞ 1/x dx → diverges
    res1 = solve_numeric_tool("integrate", expression="1/x", variable="x", bounds=[1, "inf"])
    assert res1["status"] == "error"
    assert res1["type"] == "DivergentIntegralError"

    # 2. ∫₁^∞ 1/x² dx → 1
    res2 = solve_numeric_tool("integrate", expression="1/x**2", variable="x", bounds=[1, "inf"])
    assert res2["status"] == "success"
    assert pytest.approx(res2["value"]) == 1.0
    assert res2["convergent"] is True

    # 3. ∫₀^∞ e^(-x) dx → 1
    res3 = solve_numeric_tool("integrate", expression="exp(-x)", variable="x", bounds=[0, "inf"])
    assert res3["status"] == "success"
    assert pytest.approx(res3["value"]) == 1.0
    assert res3["convergent"] is True

    # 4. ∫₀^∞ sin(x)/x dx → π/2
    res4 = solve_numeric_tool("integrate", expression="sin(x)/x", variable="x", bounds=[0, "inf"])
    assert res4["status"] == "success"
    assert pytest.approx(res4["value"]) == 1.5707963267948966
    assert res4["convergent"] is True

    # 5. ∫₀¹ 1/sqrt(x) dx → 2
    res5 = solve_numeric_tool("integrate", expression="1/sqrt(x)", variable="x", bounds=[0, 1])
    assert res5["status"] == "success"
    assert pytest.approx(res5["value"]) == 2.0
    assert res5["convergent"] is True

    # 6. ∫₀¹ 1/x dx → diverges
    res6 = solve_numeric_tool("integrate", expression="1/x", variable="x", bounds=[0, 1])
    assert res6["status"] == "error"
    assert res6["type"] == "DivergentIntegralError"

    # 7. ∫₋∞^∞ e^(-x²) dx → √π
    res7 = solve_numeric_tool("integrate", expression="exp(-x**2)", variable="x", bounds=["-inf", "inf"])
    assert res7["status"] == "success"
    assert pytest.approx(res7["value"]) == 1.772453850905516
    assert res7["convergent"] is True


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


def test_symbolic_sequences_and_series():
    """Asserts that symbolic series, summations, products, sequence limits, and convergence tests calculate correctly."""
    # 1. series: expansion of cos(x) around 0 up to order 4
    res_series = solve_symbolic_tool("cos(x)", "series", "x", extra={"point": 0, "order": 4})
    assert res_series["status"] == "success"
    assert "O(x**4)" in res_series["result_plain"] or "O(x**4" in res_series["result_plain"]

    # 2. summation: Sum of 1/n**2 from 1 to oo -> pi**2/6
    res_sum = solve_symbolic_tool("1/n**2", "summation", "n", extra={"bounds": [1, "oo"]})
    assert res_sum["status"] == "success"
    assert "pi**2/6" in res_sum["result_plain"]

    # 3. product: Product of (1 + 1/n) from 1 to 3 -> 4
    res_prod = solve_symbolic_tool("1 + 1/n", "product", "n", extra={"bounds": [1, 3]})
    assert res_prod["status"] == "success"
    assert res_prod["result_plain"] == "4"

    # 3b. product: Product of (n + 1)/n from 1 to k -> k + 1 (simplified)
    res_prod_simp = solve_symbolic_tool("(n + 1)/n", "product", "n", extra={"bounds": [1, "k"]})
    assert res_prod_simp["status"] == "success"
    assert res_prod_simp["result_plain"] == "k + 1"

    # 3c. product: Infinite Product of 1 - 1/n**2 from 2 to oo -> 1/2 (fully evaluated)
    res_prod_inf = solve_symbolic_tool("1 - 1/n**2", "product", "n", extra={"bounds": [2, "oo"]})
    assert res_prod_inf["status"] == "success"
    assert res_prod_inf["result_plain"] == "1/2"

    # 4. sequence_limit: Limit of (n + 1)/n as n -> oo is 1
    res_seq_lim = solve_symbolic_tool("(n + 1)/n", "sequence_limit", "n")
    assert res_seq_lim["status"] == "success"
    assert res_seq_lim["result_plain"] == "1"

    # 5. convergence: Sum(1/n**2, (n, 1, oo)) is convergent (True)
    res_conv1 = solve_symbolic_tool("1/n**2", "convergence", "n", extra={"bounds": [1, "oo"]})
    assert res_conv1["status"] == "success"
    assert res_conv1["result_plain"] == "True"

    # 6. convergence: Sum(1/n, (n, 1, oo)) is divergent (False)
    res_conv2 = solve_symbolic_tool("1/n", "convergence", "n", extra={"bounds": [1, "oo"]})
    assert res_conv2["status"] == "success"
    assert res_conv2["result_plain"] == "False"


def test_symbolic_solver_edge_cases():
    """Asserts that math/solver edge cases, malformed variables, syntax errors, and library errors fail gracefully."""
    # 1. Empty variable name -> MathEvaluationError
    res_empty_var = solve_symbolic_tool("1/n**2", "convergence", "", extra={"bounds": [1, "oo"]})
    assert res_empty_var["status"] == "error"
    assert res_empty_var["type"] == "MathEvaluationError"
    assert "cannot be empty" in res_empty_var["message"]

    # 2. Syntax error in expression (e.g., "sin(") -> MathSyntaxError
    res_syntax = solve_symbolic_tool("sin(", "series", "x", extra={"point": 0, "order": 5})
    assert res_syntax["status"] == "error"
    assert res_syntax["type"] == "MathSyntaxError"

    # 3. SymPy PolynomialError on invalid non-integer bounds -> MathEvaluationError (Tier 1)
    res_poly_err = solve_symbolic_tool("1/n**2", "summation", "n", extra={"bounds": [1.5, "oo"]})
    assert res_poly_err["status"] == "error"
    assert res_poly_err["type"] == "MathEvaluationError"
    assert res_poly_err["tier"] == 1

    # 4. factorial(n)/n**n convergence -> True
    res_conv_factorial = solve_symbolic_tool("factorial(n)/n**n", "convergence", "n", extra={"bounds": [1, "oo"]})
    assert res_conv_factorial["status"] == "success"
    assert res_conv_factorial["result_plain"] == "True"

    # 5. Invalid syntax n!/n**n -> MathSyntaxError (prevents AST parser recursion loop)
    res_syntax_factorial = solve_symbolic_tool("n!/n**n", "convergence", "n", extra={"bounds": [1, "oo"]})
    assert res_syntax_factorial["status"] == "error"
    assert res_syntax_factorial["type"] == "MathSyntaxError"

    # 6. Direct RecursionError serialization test -> MathEvaluationError (Tier 1)
    from core.errors import format_error
    res_recurse = format_error(RecursionError("maximum recursion depth exceeded"))
    assert res_recurse["status"] == "error"
    assert res_recurse["type"] == "MathEvaluationError"
    assert res_recurse["tier"] == 1
    assert "recursion depth" in res_recurse["message"]
