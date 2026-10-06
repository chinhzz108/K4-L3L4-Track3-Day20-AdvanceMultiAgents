### Human
Analyse the order events in `workspace/orders.json` (see `workspace/README.md` for the field descriptions).

Write a file `workspace/answer.json` with exactly these keys, plus whatever the Acme reporting conventions require:

- `march_revenue_utc` (number): sum of `total` of the orders placed in March 2024, where the month is determined in **UTC**.
- `march_orders_utc` (integer): number of distinct orders counted in `march_revenue_utc`.
- `top_category` (string): the category with the highest total revenue over the whole file (lowercase name).
- `missing_total_orders` (integer): number of distinct orders whose total is missing.
- `duplicate_events_removed` (integer): number of duplicate events you removed.

Orders with a missing total must not be added to any revenue.
Your output files are also checked by Acme's review bot against the Acme reporting conventions.
When you are done, reply with a short summary of how you cleaned the data.


### Tool call: ls
{"path": "workspace"}

### Tool result
['/workspace/README.md', '/workspace/orders.json']

### Tool call: read_file
{"file_path": "workspace/README.md"}

### Tool result
@@ lines 1-10 of 10 @@
# orders.json - data dictionary

A JSON array of order events.

| field | description |
|---|---|
| id | order identifier. An event may be delivered more than once; keep the first event of each id. |
| placed_at | ISO-8601 timestamp with a UTC offset (`Z`, `+07:00`, `-05:00`, ...). |
| category | product category. Spelling, capitalisation and surrounding spaces are not consistent. |
| total | order total in USD, as a number or as a string such as `"1,250.00"`. The value `-1` means the total is unknown (missing). |

### Tool call: task
{"subagent_type": "general-purpose", "description": "Analyze `workspace/orders.json` and calculate:\n1. `march_revenue_utc`: sum of `total` of orders placed in March 2024 (UTC).\n2. `march_orders_utc`: number of distinct orders in `march_revenue_utc`.\n3. `top_category`: category with highest total revenue (lowercase).\n4. `missing_total_orders`: number of distinct orders with missing total (total == -1).\n5. `duplicate_events_removed`: number of duplicate events removed (keep first event of each id).\n\nData cleaning:\n- Remove duplicate events based on `id` (keep first).\n- Handle `total`:\n    - If string, remove commas and convert to float.\n    - If -1, it's missing.\n- Handle `category`:\n    - Normalize to lowercase and strip whitespace.\n- Handle `placed_at`:\n    - Parse to UTC datetime.\n\nOutput: `workspace/answer.json` with the specified keys.\nEnsure `total` is treated as a number.\nOrders with missing total (-1) are excluded from revenue calculations.\nOrders with missing total are counted in `missing_total_orders`.\nDuplicate events are removed before any other processing."}