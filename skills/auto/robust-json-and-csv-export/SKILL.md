---
name: robust-json-and-csv-export
description: Use when generating output files like JSON or CSV to ensure all types, formats, currencies (cents), and metadata fields match exact specification rules.
---
- Verify exact currency formatting rules: convert dollar or decimal amounts to integer cents (multiply by 100 and round/cast to int) when requested.
- Ensure CSV files include all required headers in the exact specified order, with canonical string spelling (e.g. capitalized regions) and proper row counts.
- Add required metadata blocks (e.g., `meta` object with input source filename, raw row counts including duplicates, and rows used) to JSON outputs if requested.
- Check that all field names, keys, and schemas match expected version numbers and naming conventions (e.g. lower_case with underscores).
