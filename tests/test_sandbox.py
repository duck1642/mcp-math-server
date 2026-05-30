# -*- coding: utf-8 -*-
"""
tests/test_sandbox.py - Automated tests for the AST validation and execution sandbox.
Asserts that standard mathematical computations succeed while exploits are blocked.
"""

import pytest
from core.sandbox import run_sandboxed, validate_expression
from core.errors import SandboxSecurityError

def test_safe_mathematical_expressions():
    """Asserts that basic, safe mathematical expressions evaluate correctly."""
    assert run_sandboxed("1 + 1") == 2
    assert run_sandboxed("math.sin(0)") == 0.0
    assert run_sandboxed("np.cos(0)") == 1.0
    assert run_sandboxed("abs(-15.5)") == 15.5
    assert run_sandboxed("sum([1, 2, 3, 4])") == 10
    assert run_sandboxed("round(3.14159, 2)") == 3.14


def test_whitelisted_builtins():
    """Asserts that only whitelisted built-ins are callable."""
    assert run_sandboxed("len([1, 2, 3])") == 3
    assert run_sandboxed("min(10, 20)") == 10
    assert run_sandboxed("max(10, 20)") == 20
    assert run_sandboxed("sorted([3, 1, 2])") == [1, 2, 3]


def test_private_attribute_rejection():
    """Asserts that any attribute lookup starting with an underscore is blocked."""
    with pytest.raises(SandboxSecurityError) as exc_info:
        run_sandboxed("math.__dict__")
    assert "private attribute" in str(exc_info.value)

    with pytest.raises(SandboxSecurityError) as exc_info:
        run_sandboxed("math._private")
    assert "private attribute" in str(exc_info.value)


def test_malicious_builtins_rejection():
    """Asserts that unwhitelisted built-ins like __import__ or open are blocked."""
    with pytest.raises(SandboxSecurityError) as exc_info:
        run_sandboxed("__import__('os').system('ls')")
    assert "forbidden" in str(exc_info.value)

    with pytest.raises(SandboxSecurityError) as exc_info:
        run_sandboxed("open('file.txt', 'r')")
    assert "forbidden" in str(exc_info.value)


def test_syntax_and_assignment_rejection():
    """Asserts that variable assignments and multi-line statements throw errors."""
    with pytest.raises(SandboxSecurityError):
        run_sandboxed("x = 5")

    with pytest.raises(SandboxSecurityError):
        run_sandboxed("1 + 1; 2 + 2")


def test_execution_timeout():
    """Asserts that long-running operations are terminated by the timeout boundary."""
    # SymPy large integer calculation or a mock timeout check
    with pytest.raises(SandboxSecurityError) as exc_info:
        # A calculation that takes very long in SymPy
        run_sandboxed("sp.factorial(1000000)", timeout=0.1)
    assert "timed out" in str(exc_info.value)
