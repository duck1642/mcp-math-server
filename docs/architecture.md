# MCP Math Server — Technical Architecture Document

> A memory-first, local Model Context Protocol (MCP) server providing numerical, symbolic, dimensional, and plotting tools for engineering workflows. The default transport is local `stdio`; an optional SSE/HTTP path is available for experiments.

---

## 1. Executive Design Decisions

The MCP Math Server acts as a stateless, highly secure, mathematical co-processor for AI clients. The AI client handles reasoning and prompt formatting; this server provides exact numerical evaluation, symbolic manipulation, unit safety, and visualization.

The design prioritizes **stateless execution** and a restricted expression-evaluation surface:

1.  **Memory-First Execution Model (No "Noting"):**
    All note-taking and state-persistence capabilities (`save_note`, `load_note`, `list_notes` and `notes.json`) have been entirely stripped from the server. The AI client manages variable bindings and conversational state in its own context window. The server remains a stateless compute "skill."
2.  **Restricted Expression Evaluation:**
    Mathematical expressions are parsed and checked by an Abstract Syntax Tree (AST) allow-list. Imports, assignments, private attribute access, and non-whitelisted built-ins are rejected before evaluation.
3.  **In-Memory Plotting:**
    Plot data is rendered through Matplotlib without an application-level output file. The `plot` tool returns generated Python code; the experimental `plot_image` tool returns an in-memory PNG through MCP.

---

## 2. Technical Stack & Namespace

The mathematical core relies on standard, battle-tested Python scientific packages:

| Library | Role |
|---|---|
| `sympy` | Symbolic algebra, calculus, equation simplification |
| `numpy` | High-performance numerical arrays and linear algebra |
| `scipy` | Roots, minimization, definite integration, and ODE solvers |
| `matplotlib` | Graphic plot generation (code or in-memory PNG) |
| `pint` | Unit registration, dimensional checks, and SI conversion |
| `cmath` / `math` | Scalar complex and basic mathematics |

### Pre-loaded Namespace

All sandboxed executions run with the following namespace pre-loaded. The model writes mathematical logic using these pre-imported symbols without needing to write import statements:

```python
import sympy as sp
import numpy as np
import scipy
from scipy import linalg, integrate, optimize, signal, fft
import matplotlib
matplotlib.use('Agg')  # Force stateless, headless backend
import matplotlib.pyplot as plt
import cmath
import math
from pint import UnitRegistry
ureg = UnitRegistry()
```

---

## 3. Sandboxed Execution Engine (`core/sandbox.py`)

To prevent arbitrary execution and system exploits, numerical expressions evaluated via `calculate` and `solve_numeric` are sandboxed using an Abstract Syntax Tree (AST) compiler:

*   **Validation Method:** Expressions are parsed via `ast.parse(expression, mode="eval")`. The resulting node tree is traversed and evaluated against a strict whitelist of approved node types.
*   **Approved AST Nodes:** Literals (numbers, strings), basic binary operations (`Add`, `Sub`, `Mult`, `Div`, `Pow`, `USub`), comparison operators, list/dict/tuple comprehensions, and whitelisted function calls/attribute lookups.
*   **Attribute Access Restrictions:** Attribute lookups are limited to whitelisted attributes on approved mathematical objects. Any attribute beginning with an underscore (`_`) is rejected to prevent traversing the object graph (e.g., accessing `__class__` or `__subclasses__`).
*   **Blocked Actions:**
    *   No variable assignments or multi-line statements.
    *   No dynamic imports (`__import__` or `import` blocks are blocked).
    *   No filesystem I/O (`open()`, `read()`, `write()` are blocked).
    *   No network sockets or system-level access.
*   **Whitelisted Builtins:** `abs`, `round`, `len`, `range`, `zip`, `enumerate`, `min`, `max`, `sum`, `sorted`, `list`, `dict`, `tuple`, `bool`, `int`, `float`, `complex`, `str`.
*   **Resource Constraints:** The evaluator uses a default 10-second future timeout. There is currently no implemented memory cap, and the timeout is not a separate-process kill boundary.

---

## 4. Stateless Tool Surface

The server exposes **6 stateless tools** via FastMCP:

### 4.1 `calculate`
Evaluates a sandboxed numerical expression using numpy, scipy, cmath, or math.
*   **Parameters:**
    *   `expression` (string, required): Numerical equation to compute.
    *   `substitutions` (dict, optional): Map of variables to values (e.g., `{"F": "500 N", "L": "2 m"}`).
    *   `use_units` (boolean, optional): Set true to enable Pint unit verification.
    *   `output_unit` (string, optional): Target conversion unit (e.g., `"mm"`). Returns SI if omitted.
*   **Output:** Numeric value with unit, unit check status, and clean formatted string.

### 4.2 `solve_symbolic`
Symbolic computation using SymPy (algebra, differentiation, integration, limits, simplifications).
*   **Parameters:**
    *   `expression` (string, required): Equation or algebraic string to analyze.
    *   `operation` (string, required): One of: `solve`, `simplify`, `expand`, `diff`, `integrate`, `limit`.
    *   `variable` (string, required): Target variable (e.g., `"x"`).
    *   `domain` (string, optional): `"real"` or `"complex"` (default: `"complex"`).
    *   `extra` (dict, optional): Operation specific parameters (e.g., `{"point": "0"}` for limits).
*   **Output:** LaTeX and plain symbolic expressions. Returns all solutions when multiple are found.

### 4.3 `solve_numeric`
High-precision numerical equations, optimization, and ODE systems.
*   **Parameters:**
    *   `method` (string, required): One of: `root` (root-finding), `minimize` (optimization), `integrate` (definite integrals), `ode` (ODE systems).
    *   `expression` / `equations` (string or list, required): Mathematical system.
    *   `variable` / `variables` (string or list, required): Targets.
    *   `bounds` / `t_span` (list, optional): Numerical range.
    *   `initial` (list, optional): Initial conditions (ODE).
    *   `substitutions` (dict, optional): Variable mapping.
    *   `use_units` (boolean, optional): Applies Pint conversions.
*   **Output:** Precision values, convergence flags, and active units.

### 4.4 `check_units`
Explicit diagnostic tool for dimensional analysis and SI conversion.
*   **Parameters:**
    *   `quantities` (dict, required): Named physical variables (e.g., `{"E": "200 GPa", "I": "8.33e-6 m^4"}`).
    *   `check` (string, optional): `"compatibility"` to assert adding/multiplying safety.
    *   `expression` (string, optional): Expression for dimensional reduction.
*   **Output:** Dimensional formulas (e.g., `[mass]/([length]*[time]^2)`) and compatibility report.

### 4.5 `plot`
Generates self-contained Matplotlib code for dynamic graphics.
*   **Parameters:**
    *   `mode` (string, required): `"expression"` (computes over range) or `"data"` (uses direct array values).
    *   `expression` / `x` / `y` (string/list, required): Plotting targets.
    *   `variable` / `range` (string/list, required for expression mode).
    *   `title` / `xlabel` / `ylabel` (string, optional): Labels.
*   **Output:** JSON containing generated Matplotlib code.

### 4.6 `plot_image`
Experimental image variant of the plotting tool. It uses the same expression/data inputs as `plot` and returns a PNG through the MCP `Image` type.

*   **Output:** In-memory PNG image.

---

## 5. Physical Unit Pipeline (`core/units.py`)

To ensure mathematical consistency, Pint handles units at the **boundaries** of computations and is kept completely isolated from symbolic operations:

```
[Quantities Input] 
       ↓ 
  Parse Unit Strings & Verify Dimensional Consistency (Pint)
       ↓
  Convert all quantities to base SI equivalents
       ↓
  Extract Dimensionless Numeric Values
       ↓
  [Execute Math computation in Whitelisted Sandbox]
       ↓
  Apply Target Dimensions (or inferred SI units) to Numeric Output
       ↓
  Format Result (Return "result_si" and pretty-printed "result_pretty")
```

Trigonometric and transcendental functions (`sin`, `cos`, `tan`, `log`, `exp`) have their parameters verified to ensure they are **dimensionless** (e.g. converting degrees to radians, leaving a dimensionless float) prior to evaluation.

---

## 6. Critical Engineering Edge Cases

### A. Parser Pre-processing for Equations
*   **Gotcha:** Standard `ast.parse` in `"eval"` mode throws a `SyntaxError` when it encounters an assignment operator `=`.
*   **Solution:** Input equations containing a single `=` (not `==`) are parsed by splitting the string. `lhs = rhs` becomes a SymPy equality: `sp.Eq(lhs, rhs)`. If no equals operator exists, it is evaluated as matching zero: `sp.Eq(expression, 0)`.

### B. ODE Dynamic Lambdification
*   **Gotcha:** SciPy's `solve_ivp` requires a numerical function signature: `dy/dt = f(t, y)`. The AI writes equations as symbolic strings.
*   **Solution:** The system compiles ODE equations dynamically. It validates the AST nodes, then applies SymPy's `lambdify` function to compile the symbolic system into a sandboxed callable Python function using a NumPy backend:
    ```python
    func = sp.lambdify((t, variables), expressions, modules=['numpy', 'math'])
    ```

### C. Thread-Safe Plotting
*   **Gotcha:** STATEFUL Matplotlib calls (`plt.plot()`) share global state. Concurrent executions on background threads cause rendering crossovers.
*   **Solution:** Force the Object-Oriented Matplotlib API in `tools/plot.py`. Figures and axes are instantiated explicitly:
    ```python
    fig, ax = plt.subplots()
    ax.plot(x, y)
    # Renders fig to memory string buffer, then closes:
    plt.close(fig)
    ```

---

## 7. Two-Tier Error Pipeline (`core/errors.py`)

To keep the model self-correcting and robust:

### Tier 1 — Predictable Math Errors
Errors such as division by zero, singular matrices, unit compatibility mismatches, or AST validation failures are caught, categorized, and returned with a clean message and self-correction recommendation.
```json
{
  "status": "error",
  "tier": 1,
  "type": "unit_mismatch",
  "message": "Cannot add pressure [Pa] to velocity [m/s] — incompatible dimensions.",
  "suggestion": "Convert all terms to consistent dimensions before adding."
}
```

### Tier 2 — Unexpected System Errors
Unexpected exceptions are caught, sanitized to protect system information, and logged. A full traceback is only available when `debug=true` is set.
