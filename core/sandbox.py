# -*- coding: utf-8 -*-
"""
core/sandbox.py - Safe Abstract Syntax Tree (AST) validation and evaluation engine.
Hardens execution environment against arbitrary system calls, filesystem I/O, and exploits.
"""

import ast
import builtins
import concurrent.futures
from typing import Any, Dict, Optional
from core.errors import SandboxSecurityError
from core.namespace import SCIENCE_NAMESPACE

class SafeASTValidator(ast.NodeVisitor):
    """
    AST walker that enforces a strict whitelist of safe nodes and symbols.
    Prevents variable assignments, code imports, and object-graph traversal exploits.
    """
    def __init__(self):
        # Whitelisted AST Node Types
        self.whitelisted_nodes = {
            ast.Expression,
            ast.Constant,  # Python 3.8+ unified constant node
            ast.BinOp,
            ast.UnaryOp,
            ast.Compare,
            ast.BoolOp,
            ast.IfExp,
            ast.List,
            ast.Tuple,
            ast.Dict,
            ast.Set,
            ast.Name,
            ast.Load,
            ast.Attribute,
            ast.Call,
            # Comprehensions
            ast.ListComp,
            ast.DictComp,
            ast.SetComp,
            ast.GeneratorExp,
            ast.comprehension,
            ast.keyword,
            
            # Binary and Unary Operators
            ast.Add,
            ast.Sub,
            ast.Mult,
            ast.Div,
            ast.Mod,
            ast.Pow,
            ast.USub,
            ast.UAdd,
            
            # Comparison Operators
            ast.Eq,
            ast.NotEq,
            ast.Lt,
            ast.LtE,
            ast.Gt,
            ast.GtE,
            ast.In,
            ast.NotIn,
            ast.Is,
            ast.IsNot,
            
            # Boolean Operators
            ast.And,
            ast.Or,
        }
        
        # Add legacy nodes if present in older python versions
        for legacy_node in ["Num", "Str", "Bytes", "NameConstant"]:
            if hasattr(ast, legacy_node):
                self.whitelisted_nodes.add(getattr(ast, legacy_node))
        
        # Whitelisted built-in functions
        self.whitelisted_builtins = {
            "abs", "round", "len", "range", "zip", "enumerate",
            "min", "max", "sum", "sorted", "list", "dict", "tuple",
            "bool", "int", "float", "complex", "str"
        }

    def visit(self, node: ast.AST):
        """Validates that each node type is within the whitelist."""
        node_class = type(node)
        if node_class not in self.whitelisted_nodes:
            raise SandboxSecurityError(
                f"Use of AST node '{node_class.__name__}' is forbidden."
            )
        super().visit(node)

    def visit_Name(self, node: ast.Name):
        """Blocks private names and non-whitelisted builtins at the name level."""
        if node.id.startswith("_"):
            raise SandboxSecurityError(
                f"Access to private variable or method '{node.id}' is forbidden."
            )
        
        # If it refers to a standard builtin, check against the whitelist
        if hasattr(builtins, node.id) and node.id not in self.whitelisted_builtins:
            raise SandboxSecurityError(
                f"Use of built-in function or variable '{node.id}' is forbidden."
            )
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute):
        """Blocks access to private/double-underscore attributes to prevent escaping the sandbox."""
        if node.attr.startswith("_"):
            raise SandboxSecurityError(
                f"Access to private attribute '{node.attr}' is forbidden."
            )
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        """Checks functions called to ensure no malicious builtins are executed."""
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            if hasattr(builtins, func_name) and func_name not in self.whitelisted_builtins:
                raise SandboxSecurityError(
                    f"Use of built-in function '{func_name}' is forbidden."
                )
        self.generic_visit(node)


def validate_expression(expression: str) -> ast.Expression:
    """
    Parses a string expression and runs the SafeASTValidator on it.
    Raises SandboxSecurityError if any validation check fails or if expression has syntax errors.
    """
    clean_expr = expression.strip()
    if not clean_expr:
        raise SandboxSecurityError("Empty expression is not allowed.")
        
    try:
        # Compile in eval mode to prevent statements, imports, or assignments
        tree = ast.parse(clean_expr, mode="eval")
    except SyntaxError as e:
        raise SandboxSecurityError(f"Syntax error in mathematical expression: {e}")
        
    validator = SafeASTValidator()
    validator.visit(tree)
    return tree


def run_sandboxed(
    expression: str, 
    local_dict: Optional[Dict[str, Any]] = None, 
    timeout: float = 10.0,
    globals_dict: Optional[Dict[str, Any]] = None
) -> Any:
    """
    Validates a mathematical expression and runs it safely inside the preloaded namespace.
    Enforces a strict runtime timeout to prevent CPU lockups or infinite execution.
    """
    # 1. Parse and validate the expression
    tree = validate_expression(expression)
    
    # 2. Build the execution environment
    exec_globals = dict(globals_dict) if globals_dict is not None else dict(SCIENCE_NAMESPACE)
    eval_locals = {}
    if local_dict:
        eval_locals.update(local_dict)
        
    # Compile validated AST into callable bytecode
    code = compile(tree, "<sandbox-eval>", "eval")
    
    # 3. Run with concurrent.futures to enforce timeout
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(eval, code, exec_globals, eval_locals)
        try:
            return future.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            raise SandboxSecurityError(
                f"Execution timed out. Maximum allowable limit is {timeout} seconds."
            )
        except Exception as e:
            # Re-raise standard mathematical or custom errors directly
            raise e
