
# Engineering notes: GitGuru

## D03 - PostgreSQL

### Migrations (downgrade, current, upgrade, history)

```text
uv run alembic downgrade -1
Downgrade ff76728147ee -> 53be466b9665, add gin index on metadata

uv run alembic current
53be466b9665

uv run alembic upgrade head
Upgrade 53be466b9665 -> ff76728147ee, add gin index on metadata

uv run alembic history
53be466b9665 -> ff76728147ee (head), add gin index on metadata
<base> -> 53be466b9665, create documents and pages tables
```

### The loader is idempotent

```text
Run 1:
PASTE ACTUAL OUTPUT HERE

Run 2:
PASTE ACTUAL OUTPUT HERE

Run 3 (after editing one record):
PASTE ACTUAL OUTPUT HERE
```

### EXPLAIN for ?command=git status

```text
Normal planner:
Seq Scan on documents
Filter: (metadata @> '{"command": "git status"}'::jsonb)
Rows Removed by Filter: 19
Execution Time: 0.033 ms

With sequential scan disabled:
Bitmap Heap Scan on documents
 -> Bitmap Index Scan on ix_documents_metadata_gin
Index Cond: metadata @> '{"command": "git status"}'
Execution Time: 3.192 ms
```

### Why did PostgreSQL choose a Seq Scan?

The table contains only 20 rows, so reading the entire table is cheaper than using an index.
For a small table, index lookup can cost more than a sequential scan.

### When would it switch to the GIN index?

For larger tables or more selective JSONB filters, PostgreSQL may choose the GIN index when its estimated cost is lower.
