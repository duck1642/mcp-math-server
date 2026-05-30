# MCP Math Server

A local Model Context Protocol (MCP) server exposing scientific and symbolic math capabilities for engineering and physics workflows.

## Features
- **Stateless Symbolic Algebra & Calculus:** SymPy-backed algebraic solver, integration, derivatives, and simplification.
- **High-Precision Numerical Computations:** SciPy/NumPy dynamic solvers (roots, minimizations, integrations, ODEs).
- **Physical Unit Validation:** Pint unit registry handling conversions and dimensional consistency checks.
- **In-Memory Analytical Plotting:** File-free Matplotlib plot generator returning Base64 SVG Data URLs.
- **Hardened Security Sandbox:** AST evaluation walker with whitelisted operations and runtime limits.
