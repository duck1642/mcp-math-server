# -*- coding: utf-8 -*-
"""
tests/test_plots.py - Automated tests for the sandboxed plotting tool.
Asserts that mathematical curves and coordinate data produce valid self-contained matplotlib code.
"""

import pytest
from tools.plot import plot_tool

def test_plot_expression_mode():
    """Asserts that analytical expression curves produce valid matplotlib code."""
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
    assert "code" in res
    # Verify the generated code contains key matplotlib directives
    assert "plt.show()" in res["code"]
    assert "np.linspace" in res["code"]
    assert "sin(x)" in res["code"]
    assert "Sine Wave" in res["code"]


def test_plot_data_mode():
    """Asserts that raw coordinate arrays produce valid matplotlib code."""
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
    assert "code" in res
    # Verify the generated code embeds data and plot directives
    assert "plt.show()" in res["code"]
    assert "Square Trend" in res["code"]
    assert "0.0, 1.0, 2.0, 3.0" in res["code"]


def test_plot_image_output():
    """Asserts that the plot tool produces valid Base64 PNG data URLs when output_format is set to image."""
    res = plot_tool(
        mode="expression",
        expression="cos(x)",
        variable="x",
        range=[-3.14, 3.14, 50],
        title="Cosine",
        output_format="image"
    )
    assert res["status"] == "success"
    assert "data_url" in res
    assert "image_tag" in res
    assert "data:image/png;base64," in res["data_url"]
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
