# MCP Math Server — Implementation Roadmap

This document outlines the planned execution paths for the project, structured as feature branches.

---

## 🗺️ Feature Branches (Tracks)

### 🌿 `track/core-sandbox` — AST Hardening & Security
*   [x] Implement Abstract Syntax Tree (AST) validation in `core/sandbox.py`.
*   [x] Define the pre-loaded mathematical namespace in `core/namespace.py`.
*   [x] Enforce resource limits (execution timeouts, memory footprint caps).
*   [x] Set up whitelist rules for AST nodes, mathematical attributes, and built-ins.

### 🌿 `track/core-units` — Pint Dimensional Pipeline
*   [x] Set up Pint unit registry parsing and dimension checking in `core/units.py`.
*   [x] Implement SI base conversions for incoming inputs.
*   [x] Add validation checks to ensure transcendental/trigonometric function arguments are dimensionless.
*   [x] Construct the output formatter to attach inferred/target physical units.

### 🌿 `track/tools-numerical` — High-Precision Solvers
*   [x] Implement numerical calculation solver inside `tools/calculate.py`.
*   [x] Build SciPy/NumPy equation solvers, minimizers, and numerical integration in `tools/solve_numeric.py`.
*   [x] Add explicit dimension compatibility analysis in `tools/check_units.py`.

### 🌿 `track/tools-symbolic` — SymPy Algebra Engine
*   [x] Implement the algebraic simplification, derivation, limits, and integration solver in `tools/solve_symbolic.py`.
*   [x] Handle conversion from equation strings (containing single `=` assignments) into SymPy equations (`sp.Eq`).

### 🌿 `track/tools-plotting` — Thread-Safe Rendering
*   [x] Implement base64-encoded SVG generation using Matplotlib's Object-Oriented API in `tools/plot.py`.
*   [x] Ensure thread-safety by avoiding global Matplotlib state and explicitly closing figure objects.

### 🌿 `track/server-integration` — FastMCP Application
*   [x] Initialize the main FastMCP server in `server.py`.
*   * [x] Mount the 5 core tools onto the server instance.
*   [x] Configure robust error-handling with the Tier 1 and Tier 2 pipeline from `core/errors.py`.

### 🌿 `track/verification` — Automated Test Suite
*   [x] Fill out unit test suites under `tests/` for sandboxing, units, solvers, and plotters.
*   [x] Validate edge cases including divide-by-zero, invalid AST queries, unit mismatches, and execution timeouts.
