---
name: structured-log-parsing
description: Use when parsing messy text logs with multi-line exceptions, repeat counters, and timezone conversions to generate structured JSON outputs.
---
- Parse timestamps correctly by converting various timezone offsets or local times into unified UTC ISO-8601 format (`YYYY-MM-DDTHH:MM:SSZ`).
- Normalize service names according to rules (e.g. lowercase and replacing hyphens with underscores like `payment-service` to `payment_service`).
- Account for repeat message lines (e.g., `-- last message repeated N times --`) by incrementing repeat counts accordingly.
- Sort output entries deterministically as specified (e.g., primarily by service name, then by UTC timestamp ascending).
