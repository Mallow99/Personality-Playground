# AI tooling research library

These are the original reports saved for a later combined report, not a claim
that every researched tool is installed or tested. The review date is
2026-11-11. Preserve them as separate documents when adding new research.

- [Full stack](full-stack-2026-11-11.md): inference, optimization, model routing,
  memory, retrieval, tools, orchestration, voice/video, media, training, evaluation,
  observability, deployment, and hardware-dependent choices.
- [Memory detail](memory-2026-11-11.md): memory providers, retrieval, persistence,
  correction/deletion, and supporting tools.
- [Source catalog](sources-2026-11-11.md): 168 documentation/repository URLs and
  recorded source hashes. Links may change; hashes describe captured research
  evidence, not current upstream behavior or local performance.

`bundle.json` is the versioned import manifest. At app startup,
`bfi/knowledge.py` indexes its documents into `data/knowledge.sqlite3` using
SQLite FTS5. `/library` provides search, full text, sourced note imports, and
export. Imported notes stay in the local database; export them before moving PCs.
No embedding model, remote database, or model call is needed to search.

Full copies also live in the private Notion **BFI research library and handler
handoff**, linked from the project home. Future chats with the connection can
search that title. The app runs independently of Notion.

Read [the handler guide](../../docs/handler.md) for the implemented baseline.
Research recommendations are provisional and broader than that implementation.
