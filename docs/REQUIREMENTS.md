# Requirements: GitGuru

## Functional (what it does)

1. A user can ask a Git-related question in plain English and get an answer based on trusted Git documentation.
2. Every answer cites the source document and relevant section from which the information was retrieved.
3. If the available documents do not contain the answer, the product says "I don't know" instead of guessing.
4. Signature feature: Safe Git recovery assistant: analyze a Git problem, recommend safe recovery commands and clearly flag dangerous history-rewriting operations.
5. A user can browse and search the underlying Git documentation records through GET /v1/documents.

## Non-functional (how well, with numbers)

| # | Quality | Target | How I will measure it |
|---|---|---|---|
| 1 | Speed: record lookups | p95 under 300 ms for GET /v1/documents | Load test (Week 6) |
| 2 | Speed: answers | p95 under 4 s for a full answer; first token under 1.5 s | Traces (Week 5) |
| 3 | Accuracy | 95%+ of 40 scenario answers produce the expected repository state in the sandbox | Golden scenario test set (Weeks 4 and 5) |
| 4 | Cost | Under Rs 0.50 per answered question | LLM usage and cost tracking (Week 2) |
| 5 | Safety | Zero unflagged history-rewriting commands | Safety test suite (Weeks 4, 5 and 6) |
