
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



## Run locally in one command

You need Docker Desktop running. From a fresh clone:

```bash
docker compose up --build
```

This starts Postgres (with pgvector), Redis, runs the migrations and loads the sample data once, then starts the API.

- API docs: http://localhost:8000/docs
- Liveness: http://localhost:8000/health
- Readiness (checks the database): http://localhost:8000/ready

Stop with `Ctrl+C`, then `docker compose down`. Add `-v` to also delete the database volume.

## Develop and test

| Task | Mac / Linux | Windows |
|---|---|---|
| Run the API with reload | `make dev` | `uv run poe dev` |
| Unit tests (no network) | `make test` | `uv run poe test` |
| Integration tests (needs `docker compose up`) | `make test-integration` | `uv run poe test-integration` |
| Coverage report | `make cov` | `uv run poe cov` |
| Lint and format check | `make lint` | `uv run poe lint` |

## D04 · Docker, Compose and tests

### The image

```text
docker images gitguru:dev
[Paste the actual command output here]

docker run --rm gitguru:dev id
uid=999(app) gid=999(app) groups=999(app)
```

- Size: approximately 363 MB (target: under 400 MB)
- First build: 71.4 s. After changing one line of code: 6.5 s.
- Cached step: `uv sync --locked --no-install-project` was CACHED because dependencies are installed separately from application source code.

### The stack

```text
docker compose ps -a

NAME                IMAGE                    SERVICE   STATUS
gitguru-api-1       gitguru-api              api       Up (healthy)
gitguru-db-1        pgvector/pgvector:pg17   db        Up (healthy)
gitguru-migrate-1   gitguru-migrate          migrate   Exited (0)
gitguru-redis-1     redis:7-alpine           redis     Up (healthy)
```

Migration log after down + up:

```text
records=20 inserted=0 updated=0 unchanged=20
```

### Breaking the database on purpose

```text
db stopped:
 /health → [Paste actual output]

 /ready → HTTP 503 [Paste actual response]

db started:
 /ready → HTTP 200
{"status":"ready","checks":{"database":true}}
```

A load balancer should stop sending traffic when readiness fails because the database is unavailable. It should not restart the app because the application is still alive and can recover when the database returns.

### Tests and coverage

```text
uv run poe test
16 passed in 0.87s

uv run poe test-integration
7 passed in 14.89s

coverage TOTAL, unit only
61%

coverage TOTAL, with integration tests
67%
```

Two files my coverage report says are never run, and whether they matter:

- `src/gitguru/api/legacy_routes.py` (lines 1–31): Legacy endpoints not registered in the active application.
- `src/gitguru/api/settings.py` (lines 1–22): Used only by legacy routes; outside the active application path.


## D05 · CI/CD and going live

- Live URL: https://gitguru-qg70.onrender.com
- CI run for pull request 1: https://github.com/vishnuprasath003/prince28-dev12-gitguru/actions
- First deploy that ran by itself: https://github.com/vishnuprasath003/prince28-dev12-gitguru/actions
- Merge clicked at **Not recorded** → "Smoke test passed" at **Not recorded** → lead time: **Not recorded**

### Smoke test output from that CD run

```text
ok   /health -> 200
ok   /ready -> 200 {'status': 'ready', 'checks': {'database': True}}
ok   /v1/documents?limit=1 -> 200
Smoke test passed
```

### Rollback drill

- Rolled back to SHA **abc9c131dab2944e1600c8350c875859d37ced43**: CD Run #3 successful in **57 seconds**. Exact start and finish times: Not recorded.
- Rolled forward to SHA **66ac252615f4a71ca5704af88d32b720011a3c42**: CD Run #4 successful. Exact duration: Not recorded.
- During rollback, the database stayed on the newer schema because rollback redeployed an older application image without reversing database migrations. This is safe as long as the older application remains compatible with the newer database schema.

### Where my secrets live

- Neon string: GitHub Secret `DATABASE_URL` + Render environment. Not in Git, not in the image.
- Render deploy hook: GitHub Secret `RENDER_DEPLOY_HOOK` only.

### Monitoring

- UptimeRobot checks `/health` every 5 minutes; alerts go to my email.
- One thing that would make my live app faster on its first request: Keeping the Render service warm with regular health checks helps avoid cold-start delays on the free instance.
