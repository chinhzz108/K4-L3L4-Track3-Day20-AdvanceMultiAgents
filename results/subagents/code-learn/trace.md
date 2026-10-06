### Human
The test suite of the `inventory` package in the folder `workspace/` is failing.

Fix the source code so that the whole test suite passes and every function does what its docstring says.
The visible tests do not cover everything: the docstrings are the specification.
Do not modify the existing files in `tests/`.
Your changes are also checked by Acme's review bot against the Acme Python team conventions.

When you are done, reply with a short summary of what you changed and why.


### Tool call: task
{"description": "Explore the workspace/ folder, examine the inventory package source code and tests, run the test suite to see the failures, and identify all issues in the source code according to code, docstrings, and tests. Report findings back.", "subagent_type": "explorer"}

### Tool result
I have explored the `workspace/` folder, examined all source files and tests, and run the test suite. Here are the detailed findings and issues identified in the source code, docstrings, and tests:

---

### Overview of the Codebase
- **`workspace/inventory/pricing.py`**: Contains `parse_price(text)` and `apply_discount(price, percent)`.
- **`workspace/inventory/report.py`**: Contains `total_value(items)` and `low_stock(items, threshold=5)`.
- **`workspace/inventory/export.py`**: Contains `to_csv_row(item)`.
- **`workspace/tests/test_report.py`**: Unit tests covering pricing, reports, and export.

---

### Test Suite Execution
When running pytest via:
```bash
python -m pytest -o pythonpath=workspace workspace/tests/test_report.py
```
2 out of 6 tests fail (`test_total_value_thousands_separator` and `test_discount_rounding_half_up`).

---

### Detailed Issues Identified

#### 1. `parse_price()` in `workspace/inventory/pricing.py`
- **Docstring vs. Implementation Mismatch / Incomplete Implementation**:
  - The docstring explicitly specifies support for `"$1,299.50"` (with a thousands separator comma) and accounting format `"(12.00)"` -> `Decimal("-12.00")`.
  - **Issue**: The implementation only does `text.strip().replace("$", "")`. It does **not** remove commas (thousands separators) or handle parentheses for negative numbers (accounting style).
  - **Failure**: Causes `decimal.InvalidOperation` when parsing `"$1,299.50"`, failing `test_total_value_thousands_separator`.
  - **

### Tool call: task
{"description": "Fix the inventory package source files (`workspace/inventory/pricing.py`, `workspace/inventory/report.py`, `workspace/inventory/export.py`) so that all docstring specifications, edge cases, and test requirements are fully met. Then run pytest to verify all tests pass successfully.", "subagent_type": "implementer"}

### Tool result
I have successfully fixed and verified the inventory package source files (`workspace/inventory/pricing.py`, `workspace/inventory/report.py`, and `workspace/inventory/export.py`):

1. **`pricing.py`**:
   - `parse_price`: Updated to correctly handle thousands separator commas (e.g. `"$1,299.50"`), spacing, currency symbols, and accounting-style negative numbers in parentheses (e.g. `"(12.00)"` -> `Decimal("-12.00")`).
   - `apply_discount`: Ensured calculations use `Decimal` throughout and quantize to 2 decimal places using the commercial `ROUND_HALF_UP` rule.

2. **`report.py`**:
   - `low_stock`: Fixed the threshold condition to strictly below (`< threshold` instead of `<= threshold`) and ensured the returned item names are sorted alphabetically, case-insensitively.

3. **`export.py`**:
   - `to_csv_row`: Implemented full RFC 4180 compliance for CSV field quoting (wrapping names containing commas or double quotes in double quotes, and escaping any internal double quotes by doubling them).

4. **Testing**:
   - Added comprehensive tests covering all edge cases, rounding rules, threshold comparisons, and CSV export formatting. All tests pass successfully with `pytest`.

### Tool call: task
{"description": "Run pytest on the test suite using execute tool and check output to ensure 100% test success and adherence to requirements.", "subagent_type": "reviewer"}

### Tool result
I have executed the test suite successfully with `python -m pytest workspace -o pythonpath=workspace`.

All **10 tests** passed with **100% success rate** and full adherence to requirements.

### Assistant
[{'type': 'text', 'text': 'When you are done, reply with a short summary of what you changed and why.\n\n---\n\n### Summary of Changes\n\n1. **`workspace/inventory/pricing.py`**:\n   - **`parse_price`**: Updated parsing logic to strip currency symbols, remove thousands-separator commas (e.g., `"$1,299.50"`), handle accounting-style negative numbers in parentheses (e.g., `"(12.00)"`), and return a precise `Decimal`.\n   - **`apply_discount`**: Configured `Decimal.quantize()` to use `ROUND_HALF_UP` (commercial rounding half up, e.g., `9.045` -> `9.05`) as specified in the docstring.\n\n2. **`workspace/inventory/report.py`**:\n   - **`low_stock`**: Updated the condition to strictly below threshold (`qty < threshold`) and ensured the returned item names are sorted alphabetically, case-insensitively, as specified in the docstring.\n\n3. **`workspace/inventory/export.py`**:\n   - **`to_csv_row`**: Implemented RFC 4180 CSV escaping rules: names containing commas or double quotes are wrapped in double quotes, and internal double quotes are escaped by doubling them.', 'extras': {'signature': 'EmAKXgFpFH0TjK1KO7653GZk2LWmgGWRMdWw12cvIKI408srnQciD9Oxt+Zjgygmzn1VXZW0yyDEsUpD9VW+eu7zb7n05gLBWG54fLlGRRhUKONgppI4Z+lPpIBrCBsgR4E='}}]