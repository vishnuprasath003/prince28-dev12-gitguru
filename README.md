# GitGuru

[![CI](https://github.com/vishnuprasath003/prince28-dev12-gitguru/actions/workflows/ci.yml/badge.svg)](https://github.com/vishnuprasath003/prince28-dev12-gitguru/actions/workflows/ci.yml)

[![Live](https://img.shields.io/website?url=https%3A%2F%2Fgitguru-qg70.onrender.com%2Fhealth&label=live)](https://gitguru-qg70.onrender.com/docs)

[![Uptime (30 days)](https://img.shields.io/uptimerobot/ratio/YOUR-MONITOR-KEY)](https://gitguru-qg70.onrender.com/health)

A Git assistant that helps developers understand Git commands, solve repository problems and safely recover from Git mistakes without damaging shared history.

**Status:** Week 1 complete · Live at https://gitguru-qg70.onrender.com

**Live:** [https://gitguru-qg70.onrender.com](https://gitguru-qg70.onrender.com) · [API docs](https://gitguru-qg70.onrender.com/docs) · [health](https://gitguru-qg70.onrender.com/health)

## Who it's for

Junior developer at a Chennai product company who broke a shared branch with a force-push and is scared of rebase.

## The problem

Developers often struggle with Git commands, merge conflicts, rebasing and recovering from mistakes. A wrong command, especially a force-push or history-rewriting operation, can destroy commits or affect the entire team's shared branch.

Developers need clear explanations, safe command recommendations and guidance based on their actual repository state.

## Data sources

Official Git documentation and trusted Git learning resources.

- [Git Documentation](https://git-scm.com/docs)
- [Git Source Code](https://github.com/git/git)
- [Pro Git Book](https://github.com/progit/progit2)

## Hardest problem (my interview story)

Safe Git recovery: understanding the current repository state and recommending the correct recovery steps without losing commits or damaging shared branch history. History-rewriting commands must be clearly flagged before execution.

## Signature feature

Safe Git recovery assistant: explain a Git error, identify the repository situation, recommend the correct commands and verify the expected repository state in an isolated sandbox.

## Target metric

- 95%+ of 40 scenario answers produce the expected repository state in the sandbox.
- Zero unflagged history-rewriting commands.

## Run it locally

```bash
uv sync
cp .env.example .env
```

Windows PowerShell:

```powershell
copy .env.example .env
```

Start the application:

```bash
uv run uvicorn gitguru.api.main:create_app --factory --reload
```

Then open [http://localhost:8000/docs](http://localhost:8000/docs).

## Checks

```bash
uv run pytest
uv run ruff check .
```

## Run locally using Docker

### Start the application

```bash
docker compose up --build -d
```

The Docker Compose stack starts:

- PostgreSQL database
- Redis
- Database migrations
- GitGuru API

### Check application health

- [Health](http://localhost:8000/health)
- [Readiness](http://localhost:8000/ready)
- [API Docs](http://localhost:8000/docs)

### Development commands

```bash
uv run poe dev
uv run poe test
uv run poe test-integration
uv run poe cov
uv run poe lint
```

### Stop the application

```bash
docker compose down
```

**Windows users:** Run the commands using PowerShell. Use `uv run poe` for development tasks instead of `make`.

## CI/CD and Deployment

GitHub Actions automates continuous integration and deployment.

- CI runs on pull requests and pushes to `main`.
- Linting and tests run before the Docker image is built.
- Successful builds publish the Docker image to GitHub Container Registry.
- CD runs after successful CI on `main`.
- Database migrations run against Neon before deployment.
- Render deploys the exact commit image.
- A smoke test checks the live application after deployment.

## Production Monitoring

- **Hosting:** Render
- **Database:** Neon PostgreSQL
- **Monitoring:** UptimeRobot
- **Health endpoint:** https://gitguru-qg70.onrender.com/health
- **Monitoring interval:** Every 5 minutes

## Project Structure

```text
gitguru/
├── .github/
│   └── workflows/
│       ├── ci.yml
│       └── cd.yml
├── alembic/
├── docker/
├── scripts/
│   └── smoke.py
├── src/
│   └── gitguru/
│       └── api/
├── tests/
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── uv.lock
├── README.md
└── NOTES.md
```

## Safety Principles

- Protect shared Git history.
- Explain risky Git operations before suggesting them.
- Avoid unintentional data loss.
- Verify repository state after recovery operations.
- Keep secrets out of source code and Docker images.
