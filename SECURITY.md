# Security Policy

## Scope

This is an experimental local MCP server. Its default transport is local `stdio`. The optional SSE/HTTP path should not be exposed publicly until its transport-security configuration has been reviewed.

The expression validator is a validation layer, not a separate process or a memory-isolated security boundary.

## Reporting a vulnerability

Please do not report security vulnerabilities in public issues.

Use GitHub's private vulnerability reporting or security advisory features when available. If those options are unavailable, contact the maintainer through the [@duck1642 GitHub profile](https://github.com/duck1642).

Include, when possible:

- a short description of the vulnerability and its impact,
- clear reproduction steps or a minimal proof of concept,
- the affected commit or version,
- relevant logs with credentials, tokens, and private paths removed.

There is no formal response-time guarantee for this experimental project, but reports will be reviewed as soon as practical.
