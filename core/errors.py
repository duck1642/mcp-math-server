# -*- coding: utf-8 -*-
"""
core/errors.py - Error handling and exception serialization pipeline.
Defines predictable math/sandbox errors (Tier 1) and handles system failures (Tier 2).
"""

import traceback

class MathServerException(Exception):
    """Base exception for all predictable math server errors."""
    def __init__(self, message, suggestion=None):
        super().__init__(message)
        self.message = message
        self.suggestion = suggestion or "Check the input parameters and expression syntax."

class SandboxSecurityError(MathServerException):
    """Raised when an expression violates sandbox safety limits or AST validation."""
    def __init__(self, message, suggestion=None):
        default_suggestion = (
            "Ensure the expression only uses approved mathematical functions and operators. "
            "Filesystem access, system calls, variable assignments, and double underscore attributes are forbidden."
        )
        super().__init__(message, suggestion or default_suggestion)

class UnitMismatchError(MathServerException):
    """Raised when units are physically incompatible or dimension checks fail."""
    def __init__(self, message, suggestion=None):
        default_suggestion = (
            "Verify that all added, subtracted, or compared quantities have matching dimensions "
            "(e.g., converting pressure [Pa] to velocity [m/s] is physically invalid)."
        )
        super().__init__(message, suggestion or default_suggestion)

class MathEvaluationError(MathServerException):
    """Raised when evaluation fails due to domain limits, division by zero, or solver failures."""
    def __init__(self, message, suggestion=None):
        super().__init__(message, suggestion)

class MathSyntaxError(MathServerException):
    """Raised when a mathematical expression is syntactically invalid."""
    def __init__(self, message, suggestion=None):
        default_suggestion = (
            "Review the mathematical operator formatting. "
            "Ensure standard mathematical operators (*, /, +, -, **) are correctly placed "
            "and all parenthesis or brackets are fully closed."
        )
        super().__init__(message, suggestion or default_suggestion)

class DivergentIntegralError(MathServerException):
    """Raised when a numerical or symbolic integral diverges or fails to converge."""
    def __init__(self, message, suggestion=None):
        default_suggestion = (
            "Check the integration boundaries and the behavior of the integrand at the bounds "
            "or singularities. Ensure the improper integral converges mathematically."
        )
        super().__init__(message, suggestion or default_suggestion)

def format_error(error: Exception, debug: bool = False) -> dict:
    """
    Serializes an exception into a clean, structured JSON response dictionary.
    Differentiates between Tier 1 (predictable) and Tier 2 (unexpected) exceptions.
    """
    if isinstance(error, MathServerException):
        return {
            "status": "error",
            "tier": 1,
            "type": error.__class__.__name__,
            "message": error.message,
            "suggestion": error.suggestion
        }
    
    # Handle known standard predictable mathematical exceptions and map them to Tier 1
    if isinstance(error, ZeroDivisionError):
        return {
            "status": "error",
            "tier": 1,
            "type": "ZeroDivisionError",
            "message": "Division by zero encountered in expression.",
            "suggestion": "Check denominators or variables to prevent division by zero."
        }
    
    # Check for Pint dimensional errors dynamically if Pint is imported
    error_class_name = error.__class__.__name__
    if "DimensionalityError" in error_class_name:
        return {
            "status": "error",
            "tier": 1,
            "type": "UnitMismatchError",
            "message": str(error),
            "suggestion": "Convert all quantities to compatible physical dimensions before operating."
        }
    
    # Tier 2: Unexpected System Error
    response = {
        "status": "error",
        "tier": 2,
        "type": error_class_name,
        "message": "An unexpected system error occurred during execution."
    }
    
    if debug:
        # Enforce UTF-8 serialization of tracebacks
        response["traceback"] = "".join(
            traceback.format_exception(type(error), error, error.__traceback__)
        )
    else:
        response["suggestion"] = "Please contact the system administrator or check logs for internal details."
        
    return response
