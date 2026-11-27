
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
- Rolled forward to SHA **66ac252615f4a71ca5704c vaf88d32b720011a3c42**: CD Run #4 successful. Exact duration: Not recorded.
- During rollback, the database stayed on the newer schema because rollback redeployed an older application image without reversing database migrations. This is safe as long as the older application remains compatible with the newer database schema.

### Where my secrets live

- Neon string: GitHub Secret `DATABASE_URL` + Render environment. Not in Git, not in the image.
- Render deploy hook: GitHub Secret `RENDER_DEPLOY_HOOK` only.

### Monitoring

- UptimeRobot checks `/health` every 5 minutes; alerts go to my email.
- One thing that would make my live app faster on its first request: Keeping the Render service warm with regular health checks helps avoid cold-start delays on the free instance.



## D06 · Collecting the corpus

- Start target: Reference pages for the 40 most-used commands + Pro Git chapters 1-3 and 7
- Collected today: ___ files, ___ pages, ___ MB (from DATASET.md)
- Doors used: URL list / Git repository / sitemap / by hand (keep the ones I used)

### Licence check

| Source | Licence or terms, in my words | May I show full text in answers? |
|---|---|---|
| | | |

### robots.txt

- Site: ________ . Its robots.txt says (2 lines): ________
- Was anything blocked for my bot? What did I do about it?

### Kill and resume

- Run 1: I pressed Ctrl+C after ___ files
- Run 2: downloaded=___ skipped=___
- Run 3: downloaded=0 skipped=___

### Capacity (from docs/CAPACITY.md)

- Tokens per page, measured: ___
- Full corpus: ___ M tokens, ___ chunks, embedding about Rs ___, vectors ___ MB
- The number that surprised me most, and why (2 lines):

### One thing that went wrong today, and how I fixed it

<!-- D07 parser comparison:start -->
### D07 · Parser comparison

| File | Parser | Status | Pages | Characters | Headings | Tables | Seconds | Choice / reason |
|---|---|---|---:|---:|---:|---:|---:|---|
| data\raw\git-docs\git-log-0d527d8c.html | Trafilatura | OK | 26 | 111182 | 62 | 0 | 2.632 | |
| data\raw\git-docs\git-log-0d527d8c.html | Plain HTML tag stripping | OK | 1 | 109418 | 0 | 0 | 0.185 | |
| data\raw\git-docs\git-rebase-48abaed1.html | Trafilatura | OK | 17 | 58073 | 34 | 0 | 0.832 | |
| data\raw\git-docs\git-rebase-48abaed1.html | Plain HTML tag stripping | OK | 1 | 58181 | 0 | 0 | 0.111 | |
| data\raw\git-docs\git-merge-b49a020a.html | Trafilatura | OK | 11 | 36636 | 20 | 0 | 0.878 | |
| data\raw\git-docs\git-merge-b49a020a.html | Plain HTML tag stripping | OK | 1 | 37546 | 0 | 0 | 0.075 | |
| data\raw\git-docs\git-commit-70d457fa.html | Trafilatura | OK | 8 | 29620 | 14 | 0 | 0.691 | |
| data\raw\git-docs\git-commit-70d457fa.html | Plain HTML tag stripping | OK | 1 | 29967 | 0 | 0 | 0.05 | |
| data\raw\git-docs\git-branch-2c009f25.html | Trafilatura | OK | 7 | 25607 | 12 | 0 | 0.587 | |
| data\raw\git-docs\git-branch-2c009f25.html | Plain HTML tag stripping | OK | 1 | 25744 | 0 | 0 | 0.068 | |
| data\raw\git-docs\git-status-14fc55bf.html | Trafilatura | ERROR: TypeError: object of type 'int' has no len() | 0 | 0 | 0 | 0 | 0.547 | |
| data\raw\git-docs\git-status-14fc55bf.html | Plain HTML tag stripping | OK | 1 | 21083 | 0 | 0 | 0.064 | |
| data\raw\git-docs\git-add-6266f910.html | Trafilatura | OK | 6 | 17814 | 10 | 0 | 0.377 | |
| data\raw\git-docs\git-add-6266f910.html | Plain HTML tag stripping | OK | 1 | 19094 | 0 | 0 | 0.028 | |
| data\raw\git-docs\git-reset-fdf3b046.html | Trafilatura | OK | 6 | 19034 | 10 | 0 | 0.394 | |
| data\raw\git-docs\git-reset-fdf3b046.html | Plain HTML tag stripping | OK | 1 | 20271 | 0 | 0 | 0.055 | |
| data\raw\git-docs\git-switch-5da70052.html | Trafilatura | OK | 4 | 11725 | 6 | 0 | 0.277 | |
| data\raw\git-docs\git-switch-5da70052.html | Plain HTML tag stripping | OK | 1 | 12682 | 0 | 0 | 0.042 | |
| data\raw\git-docs\git-restore-ad3d46f7.html | Trafilatura | OK | 3 | 8087 | 4 | 0 | 0.224 | |
| data\raw\git-docs\git-restore-ad3d46f7.html | Plain HTML tag stripping | OK | 1 | 9110 | 0 | 0 | 0.029 | |

Fill the **Choice / reason** column manually after inspecting the output.

Inspect at least three files next to their parsed pages. Check table quality, heading accuracy, unwanted boilerplate, character quality, and parsing speed.

<!-- D07 parser comparison:end -->

## D07 · Parser comparison

<!-- parsers:start -->
| File | Parsers (A / B) | Pages | A found | B found | Time (A / B) | Better, why |
|---|---|---|---|---|---|---|
| git-log-0d527d8c.html | trafilatura / strip tags | 26 | 111,207 chars, 28 headings, 0 tables | 112,866 chars, 0 headings, 0 tables | 2.28 s / 0.07 s | |
| git-rebase-48abaed1.html | trafilatura / strip tags | 17 | 58,089 chars, 40 headings, 0 tables | 58,971 chars, 2 headings, 0 tables | 0.55 s / 0.03 s | |
| git-merge-b49a020a.html | trafilatura / strip tags | 11 | 36,646 chars, 26 headings, 0 tables | 38,555 chars, 0 headings, 0 tables | 0.47 s / 0.02 s | |
| git-commit-70d457fa.html | trafilatura / strip tags | 8 | 29,627 chars, 24 headings, 0 tables | 31,028 chars, 1 headings, 0 tables | 0.38 s / 0.02 s | |
| git-branch-2c009f25.html | trafilatura / strip tags | 7 | 25,613 chars, 21 headings, 0 tables | 27,085 chars, 0 headings, 0 tables | 0.35 s / 0.02 s | |
| git-status-14fc55bf.html | trafilatura / strip tags | 8 | 20,227 chars, 28 headings, 4 tables | 22,138 chars, 5 headings, 0 tables | 0.31 s / 0.02 s | |
| git-add-6266f910.html | trafilatura / strip tags | 6 | 17,819 chars, 21 headings, 0 tables | 19,541 chars, 0 headings, 0 tables | 0.23 s / 0.01 s | |
| git-reset-fdf3b046.html | trafilatura / strip tags | 6 | 19,039 chars, 19 headings, 0 tables | 20,148 chars, 0 headings, 0 tables | 0.43 s / 0.01 s | |
| git-switch-5da70052.html | trafilatura / strip tags | 4 | 11,728 chars, 19 headings, 0 tables | 13,265 chars, 0 headings, 0 tables | 0.20 s / 0.01 s | |
| git-restore-ad3d46f7.html | trafilatura / strip tags | 3 | 8,089 chars, 18 headings, 0 tables | 9,591 chars, 0 headings, 0 tables | 0.24 s / 0.01 s | |
<!-- parsers:end -->


### D07 · Parsing my corpus

- Files in the manifest: 966
- Parsed: 966
- Failed: 0
- Pages in Postgres: 2642
- Parsing coverage: 100%

### Failures by reason

| Reason | Files | What I did |
|---|---:|---|
| Current failures | 0 | All files parsed successfully after retry |

- The one I fixed: `data/raw/git-repo/Documentation/git-filter-branch.adoc`
- Reason: `parse_error`
- Fix: Fixed the parser issue and successfully retried the file.

### What I saw when I read my parsed pages

- A page where the heading path is right (document, page, path): [FILL AFTER INSPECTION]
- Something that came out wrong (document, page, what): [FILL AFTER INSPECTION]
- A table: Markdown grid or loose text? (document, page): [FILL AFTER INSPECTION]

### My parser choice

- For PDFs I use [FILL AFTER PDF COMPARISON] because [REASON].
- A kind of document in my corpus that neither parser handles well: [FILL AFTER INSPECTION]

### One thing that went wrong today, and how I fixed it

The `git-filter-branch.adoc` file failed during parsing due to a database connection issue while inserting pages. I fixed the issue and successfully retried the file.

# Day 8 · LLM Gateway

### LLM Gateway

- Primary: `gemini-3.5-flash` (Gemini)
- Fallback: `openai/gpt-oss-20b` (Groq)
- First question on my laptop: total **12.62 s**, tokens in **179** / out **164**, cost **Rs 0.000000**
- JSON request: total **12.62 s**, tokens in **179** / out **164**, cost **Rs 0.000000**

### Tokens: English against Tamil

| Message                                  | Tokens in |
| ---------------------------------------- | --------: |
| "Hi" (baseline: mostly my system prompt) |       168 |
| The English sentence                     |       176 |
| The same sentence in Tamil               |       252 |

- English content tokens: **8** (176 - 168)
- Tamil content tokens: **84** (252 - 168)
- Tamil needs **10.5x** tokens compared to English.
- Note: English used Gemini; Tamil used Groq fallback, so this is not an exact apples-to-apples comparison.

### What the model does without my documents

- **Q6:** Asked who pushed to the company's main branch last night. The model admitted it does not have access to the repository and was unsure. **Good uncertainty admission.**
- **Off-topic question:** Asked who won the 2011 Cricket World Cup. The model declined with one sentence saying the question was outside GitGuru's scope.
- **Additional Git question:** Asked what `git reset --hard` does and what happens to uncommitted changes. The answer was generally correct but included a misleading recovery claim about using the reflog to recover discarded changes.
- **Document question 1:** Asked what GitGuru's project documentation contains about Git operations and dangerous commands. The model admitted that project documentation was not connected, did not invent document details, and clearly separated general Git knowledge.
- **Document question 2:** Asked what GitGuru documentation says about handling merge conflicts. The model again admitted that documents were not connected and explained standard Git merge-conflict resolution separately.
- **Result:** Both document-based questions passed the uncertainty check. No invented project-document content was detected.

### Fallback and circuit breaker

- Set `LLM_PRIMARY_MODEL=gemini-no-such-model` to intentionally break the primary model.
- First three requests: Gemini returned 404 errors; Groq fallback succeeded.
- From request 4 onward, the circuit breaker opened and skipped Gemini, sending requests directly to Groq.
- After waiting 30 seconds, tested the half-open state.
- Half-open test: first words after **5.10 s**, total **6.93 s**, tokens in **241** / out **202**, fallback **YES**.
- Removed the invalid model configuration and restarted the server.
- Restored primary test: Gemini `gemini-3.5-flash`, first words after **20.36 s**, total **25.87 s**, tokens in **179** / out **159**, fallback **NO**.

### The bill

- `/v1/usage` dashboard:
  - Total calls: **23**
  - Errors: **8**
  - Fallbacks: **9**
  - Total cost: **Rs 0.0949**
  - Input tokens: **3,274**
  - Output tokens: **3,453**
- Average cost per successful recorded provider call: approximately **Rs 0.00633**.
- Day 1 cost target: **under Rs 0.50 — PASS**

### One thing that went wrong today, and how I fixed it

- Deliberately configured an invalid Gemini model to test fallback.
- Gemini returned 404 errors.
- Groq fallback continued answering successfully.
- Circuit breaker opened after repeated primary failures and skipped Gemini.
- Waited 30 seconds to test half-open behavior.
- Removed the invalid model configuration and restarted the server.
- Verified Gemini primary was restored and fallback was NO.
- Added the prompts directory to the Docker image using:
  `COPY --chown=app:app prompts ./prompts`

## D09 · Prompt versions compared

<!-- prompts:start -->

| Prompt version | Correct | Accuracy | Invalid replies | Avg tokens in |
|---|---|---|---|---|
| classify_v1 | 13/20 | 65% | 0 | 112 |
| classify_v2 | 19/20 | 95% | 0 | 279 |
| classify_v3 | 19/20 | 95% | 0 | 367 |
| classify_v4 | 20/20 | 100% | 0 | 390 |

<!-- prompts:end -->

### D09 · Prompts and structured output

- My best router prompt: classify_v4 with 20 / 20
- What I changed in v4, and what happened to the score: Improved the prompt instructions and classification boundaries; accuracy reached 100%.
- The question my best version still gets wrong: None in the 20-question test set.
- A label in my test set that I changed after seeing the results: None.
- Input tokens per question: v1 112, best version v4 390. The extra accuracy is worth it for the current test set, but v4 uses more tokens.

### My contract (DocMeta)

- Fields I kept from my project card: command, option, topic, git_version, section, with document-level fields such as doc_kind, year, language, summary and topics.
- Fields I deleted, and why they make no sense per document: source, because source information already exists in the document system.
- The field I tightened, and how: doc_kind was constrained to predefined document categories using Literal values.

### Extraction run

- Prompt version: extract_v1 · documents: 230 ok, 0 repaired, 1 failed (of 231 processed)
- Not finished? Why, and how many are left: 231 of 966 documents processed; 735 remaining. Extraction is resumable.
- Most common failure reason, and what I did about it: 1 document failed; failure reason not investigated yet.
- A record that was valid but wrong (document, field, what it said, what is true): Not manually verified yet.
- Cost at list price: Rs 0.1817 for the initial 5-document run; total cost for 231 documents not yet calculated.


### One thing that went wrong today, and how I fixed it

- Metadata extraction was interrupted by provider rate limits and temporary server errors. The extraction process is resumable, so successful documents remain saved and the remaining documents can be processed later.
- The live API check returned 404 for the documents route. Render is running a manually deployed commit from main, so the Day 9 API changes may not be deployed yet.

## Manual Metadata Verification

Manually inspected 5 document metadata records from the database to check
whether the extracted metadata fields were populated and reasonably consistent.

| Document ID | Document / Command | Fields Checked | Status |
|---|---|---|---|
| 000f261e-738f-4a5a-8108-b05acbeab4ec | Git 2.3.10 Release Notes | Summary, topics, Git version | Partial |
| 000f65d0-c160-41f5-a027-65f1401ff887 | Git 1.7.2.5 Release Notes | Summary, Git version, section | Partial |
| 00b88798-6d7d-47b3-bdd1-1497788f8206 | git-unpack-file | Summary, command, topics | Partial |
| 015cc4da-bef2-4288-9531-f9c87bb5ebe2 | git-ls-files | Summary, command, topics, options | Partial |
| 01a9394d-18d1-4a76-881a-d447645b868f | Git web configuration | Summary, command, topics | Partial |

### Verification Notes

- Inspected metadata records directly from the database.
- Checked document titles, summaries, document kinds, commands, topics,
  Git versions, sections and available options.
- The extracted metadata appeared reasonably consistent for the inspected records.
- This was a metadata consistency check; the records were not fully compared
  against their original source documents.
- Therefore, the verification is considered partial rather than complete.

## Metadata Extraction Progress

- Total corpus: 966 documents
- Metadata extraction script: `scripts/extract_metadata.py`
- Prompt version: `extract_v1`
- Extraction is resumable; previously processed documents are skipped.
- More than 160 documents have been processed across multiple runs.
- Extraction is incomplete due to API rate limits and temporary provider errors (Gemini 429/503 and Groq 429).
- Latest reported run: 94 successful, 8 repaired, 0 failed.
- Remaining pending documents: 884 (at the latest reported run).
- Extraction will be resumed when API rate limits allow.

### Manual Metadata Verification

Manually inspected 5 metadata records from the database.

| Document | Metadata checked | Verification |
|---|---|---|
| Git 2.3.10 Release Notes | Summary, topics, Git version | Partial |
| Git 1.7.2.5 Release Notes | Summary, Git version, section | Partial |
| git-unpack-file | Summary, command, topics | Partial |
| git-ls-files | Summary, command, topics, options | Partial |
| Git web configuration | Summary, command, topics | Partial |

- Checked whether metadata fields were populated and reasonably consistent.
- This was a database metadata consistency check.
- The original source documents were not fully compared, so verification is marked partial.
