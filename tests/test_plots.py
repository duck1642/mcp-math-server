# -*- coding: utf-8 -*-
"""
tests/test_plots.py - Automated tests for the thread-safe in-memory plotting engine.
Asserts that mathematical curves and coordinate data generate valid inline SVGs.
"""

import pytest
from tools.plot import plot_tool

def test_plot_expression_mode():
    """Asserts that analytical expression curves render to Base64 SVG Data URLs."""
    res = plot_tool(
        mode="expression",
        expression="sin(x)",
        variable="x",
        range=[-3.14, 3.14, 50],
        title="Sine Wave",
        xlabel="Angle (rad)",
        ylabel="Amplitude"
    )
    assert res["status"] == "success"
    assert res["mode"] == "expression"
    # Ensure it generated inline markdown and data URL
    assert "data:image/svg+xml;base64," in res["data_url"]
    assert "![plot]" in res["image_tag"]


def test_plot_data_mode():
    """Asserts that raw coordinate arrays render correctly to Base64 SVG Data URLs."""
    res = plot_tool(
        mode="data",
        x=[0, 1, 2, 3],
        y=[0, 1, 4, 9],
        title="Square Trend",
        xlabel="X coordinate",
        ylabel="Y coordinate"
    )
    assert res["status"] == "success"
    assert res["mode"] == "data"
    assert "data:image/svg+xml;base64," in res["data_url"]
    assert "![plot]" in res["image_tag"]


def test_plotting_exceptions():
    """Asserts that bad ranges or missing arguments raise errors gracefully."""
    # Invalid mode
    res_bad_mode = plot_tool(mode="unknown")
    assert res_bad_mode["status"] == "error"

    # Mismatched sizes in data mode
    res_bad_size = plot_tool(mode="data", x=[1, 2], y=[1])
    assert res_bad_size["status"] == "error"

    # Invalid range in expression mode
    res_bad_range = plot_tool(mode="expression", expression="x**2", variable="x", range=[5, 1])
    assert res_bad_range["status"] == "error"
