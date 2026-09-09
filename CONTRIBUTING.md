# Contributing

Contributions that improve the server's correctness, documentation, tests, or MCP tool behavior are welcome.

## Before opening an issue

- Search existing issues first.
- Include the operating system, Python version, MCP client, and the exact command or configuration involved.
- Provide a minimal reproducible example when possible.
- Do not include private paths, credentials, tokens, or other sensitive data.

## Local development

1. Create and activate a virtual environment.
2. Install the dependencies:

   ```text
   python -m pip install -r requirements.txt
   ```

3. Run the test suite:

   ```text
   python -m pytest -q
   ```

4. Start the local server when manual verification is needed:

   ```text
   python server.py
   ```

## Pull requests

- Keep changes focused and explain the user-facing effect.
- Update the README or other documentation when behavior changes.
- Add or update tests for functional changes where practical.
- Confirm that the test suite passes before opening the pull request.
- Clearly note known limitations, security considerations, or follow-up work.
