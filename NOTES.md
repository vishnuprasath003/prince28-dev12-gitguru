# GitGuru - Day 03 Notes

## Database
- PostgreSQL connected through SQLAlchemy async engine.
- Documents and pages tables created using Alembic.

## Migrations
- Initial migration: 53be466b9665
- GIN migration: ff76728147ee
- GIN index: ix_documents_metadata_gin

## Loader
- Script: scripts/load_db.py
- First run output: TODO
- Second run output: TODO
- Updated-record test: TODO

## API
- Documents API: TODO
- Filters: command, topic, source, git_version
- Readiness endpoint: TODO

## Tests
- Current result: 8 passed
- Target: 16 unit tests

## EXPLAIN
- Run: uv run python scripts/explain.py
- Query plan: TODO
- Explanation: TODO
