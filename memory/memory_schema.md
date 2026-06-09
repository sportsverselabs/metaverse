# Memory Schema (Shell)

> Defines how Sportsverse OS agents remember things. Portable, file-based, inspectable.
> Shell only — no memory store is active yet (Phase 1+). Last updated: 2026-06-08

---

## 1. Principles

- **File-based & portable:** memories are plain files inside `memory/`, so they move with the project.
- **One fact per file:** small, focused, easy to update or delete.
- **No secrets in memory:** never store API keys, passwords, or tokens here.
- **Inspectable:** a human can open any memory file and understand it.

## 2. Layout (planned)

```
memory/
├─ memory_schema.md     ← this file (the rules)
├─ index.md             ← one-line pointer per memory (the table of contents)
└─ store/               ← the actual memory files (gitignored if they hold private data)
   └─ .gitkeep
```

> `store/` and `index.md` are created when memory goes live in Phase 1.

## 3. Memory file format

Each memory file is Markdown with frontmatter:

```markdown
---
name: <short-kebab-case-slug>
description: <one-line summary used to judge relevance>
type: owner | feedback | project | reference | agent
created: <YYYY-MM-DD>
updated: <YYYY-MM-DD>
owner_agent: <which agent owns this memory, e.g. hermes>  # optional
---

<the fact, in plain language. Link related memories with [[other-name]].>
```

## 4. Memory types

| Type | Stores | Example |
|---|---|---|
| `owner` | Facts about the owner / preferences | "Owner prefers low-cost open-source tools." |
| `feedback` | Guidance/corrections on how to work | "Always update the handoff file before stopping." |
| `project` | Ongoing work, goals, constraints | "Phase 0 must finish before any agent is built." |
| `reference` | Pointers to external resources | "Sports data API docs: <url>." |
| `agent` | Things a specific agent must remember | "OpenClaw only acts on Hermes-delegated tasks." |

## 5. The index

`memory/index.md` holds one line per memory so an agent can scan relevance fast:

```
- [Title](store/file.md) — one-line hook
```

## 6. Rules for agents using memory

1. Before saving, check the index for an existing file that already covers it — update instead of duplicating.
2. Use absolute dates (`2026-06-08`), never "today".
3. Delete memories that turn out to be wrong.
4. Don't store what the code or these docs already record.
5. Never store secrets or personal data without an owner-approved reason.

## 7. Status

- Schema: ✅ defined (this file)
- Active store: ⛔ not created yet (Phase 1)
- Wiring into agents: ⛔ not built yet (Phase 1)
