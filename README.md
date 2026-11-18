# GitGuru

A Git assistant that helps developers understand Git commands, solve repository problems and safely recover from Git mistakes without damaging shared history.

**Status:** Day 1 foundation (uv project, project documentation and quality gates). Live URL from Day 5.

## Who it's for

Junior developer at a Chennai product company who broke a shared branch with a force-push and is scared of rebase.

## The problem

Developers often struggle with Git commands, merge conflicts, rebasing and recovering from mistakes. A wrong command, especially a force-push or history-rewriting operation, can destroy commits or affect the entire team's shared branch.

Developers need clear explanations, safe command recommendations and guidance based on their actual repository state.

## Data sources

Official Git documentation and trusted Git learning resources.

- https://git-scm.com/docs
- https://github.com/git/git (Documentation/)
- https://github.com/progit/progit2

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
cp .env.example .env   # Windows: copy .env.example .env
uv run uvicorn gitguru.api.main:create_app --factory --reload
```

Then open http://localhost:8000/docs

## Checks

```bash
uv run pytest
uv run ruff check .
```
