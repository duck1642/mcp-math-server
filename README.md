# MCP Math Server

An experimental local Model Context Protocol (MCP) server for scientific, symbolic, numerical, and dimensional mathematics in engineering and physics workflows.

The default transport is local `stdio`. The server is stateless and does not provide a persistent notes or file-management layer.

## Features

- **Symbolic mathematics:** SymPy-backed solving, simplification, expansion, differentiation, integration, and limits.
- **Numerical methods:** NumPy/SciPy-backed calculation, root finding, minimization, definite integration, and ODE solving.
- **Dimensional analysis:** Pint-based unit parsing, compatibility checks, and conversions.
- **Plotting:** Generate self-contained Matplotlib code with `plot`, or request an in-memory PNG through the experimental `plot_image` tool.
- **Expression validation:** Mathematical expressions are checked by an AST allow-list before evaluation and have a default execution timeout.

## Requirements

Install the dependencies in an environment with Python and `pip`:

```text
python -m pip install -r requirements.txt
```

## Running locally

Start the server with the default local transport:

```text
python server.py
```

For an MCP client, copy `mcp_config_template.json` and replace the example server path with the absolute path to this repository. The template intentionally contains no machine-specific path.

The source also contains an optional SSE/HTTP launch path for local experiments. It should not be exposed publicly until its transport-security configuration is hardened.

## Available tools

| Tool | Purpose |
|---|---|
| `calculate` | Evaluate numerical expressions, optionally with units. |
| `solve_symbolic` | Perform symbolic algebra and calculus operations. |
| `solve_numeric` | Run numerical root, optimization, integration, and ODE methods. |
| `check_units` | Inspect dimensional compatibility and conversions. |
| `plot` | Return self-contained Matplotlib plotting code. |
| `plot_image` | Experimental: return an in-memory PNG as an MCP image. |

## Testing

```text
python -m pytest -q
```

## Security scope

The AST validator blocks imports, assignments, private attribute access, and non-whitelisted built-ins. This is an expression-validation layer, not a separate process or a memory-isolated security boundary. The optional SSE/HTTP path should be treated as local/test-only until it is reviewed separately.
