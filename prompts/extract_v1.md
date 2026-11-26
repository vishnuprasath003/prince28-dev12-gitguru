You read one document from GitGuru's collection and fill in a small record about it.

What GitGuru does: A Git expert that answers from the official Git reference and the Pro Git book, and proves every command in a throwaway repository before showing it.

Rules:
- Reply with one JSON object and nothing else: no explanation, no Markdown fences.
- Use only what the document says. If it does not say, use null for the year and [] for a list.
- summary: one or two plain sentences, at most 300 characters.
- topics: 1 to 6 short topics.
- Every list holds short values copied from the document, at most 8.

What each field means:
- doc_kind: what kind of document this is.
- year: the year it was published or came into force.
- language: the main language of the text (en, ta, hi or other).
- command: every "command" this document is mainly about.
- option: every "option" this document is mainly about.
- topic: every "topic" this document is mainly about.
- git_version: every "git version" this document is mainly about.
- section: every "section" this document is mainly about.
