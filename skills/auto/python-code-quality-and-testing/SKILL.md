---
name: python-code-quality-and-testing
description: Use when modifying Python packages or modules to guarantee that all public functions have type hints, regression tests are added, and changes are logged.
---
- Add type annotations to all parameters and return values for every public function (any name not starting with an underscore `_`).
- Create or update a regression test file (e.g., `tests/test_regressions.py`) containing at least one test function per bug or feature fix.
- Record every bug fix or feature update in `CHANGELOG.md` under the heading `## Unreleased` using the bullet format `- fix(<function name>): <short description>`.
- Run the full test suite (e.g., via pytest) after making code changes to verify zero regressions.
