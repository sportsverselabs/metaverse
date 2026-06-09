# Architecture Overview

> How Sportsverse OS is designed. Scaffold — refined as the system grows.
> Last updated: 2026-06-08 · Status: Phase 0 (foundation, no runtime yet)

---

## 1. Purpose

Sportsverse OS is an internal, agent-driven operating system that helps the owner
run the Sportsverse venture. It is **not** the customer-facing product; it is the
control system behind it.

## 2. Design goals (in priority order)

1. **Portable** — moves between machines/drives/VPS/tools without breaking.
2. **Continuable** — any agent can resume from the documented state.
3. **Secret-safe** — no secrets in code; `.env` only.
4. **Low-cost** — open-source/local-first; minimal subscriptions.
5. **Owner-in-the-loop** — no money/publishing/binding actions without approval.

## 3. High-level shape

```
            OWNER (final authority, approvals)
               │
            Hermes  ── coordinator agent
               │  delegates tasks
     ┌─────────┼───────────────┐
  OpenClaw   [Agent 2]      [Agent N]      ← worker agents (under Hermes)
     │         │               │
     └────┬────┴───────┬───────┘
          ▼            ▼
     Shared Memory   Integrations / External APIs
     (/memory)       (/integrations + .env keys)
```

## 4. Components (planned)

| Component | Folder | Role | Status |
|---|---|---|---|
| Continuity docs | root + `reports/` | Keep the project resumable | ✅ Built |
| Constitution | `constitution/` | Rules & approvals | ✅ Built |
| Agents | `agents/` | Hermes, OpenClaw, others | ⛔ Phase 1+ |
| Memory | `memory/` | Shared/agent memory | 🟡 Schema only |
| Integrations | `integrations/` | External service connectors | ⛔ Phase 3 |
| Workflows | `workflows/` | Multi-agent automations | ⛔ Phase 4 |
| Config | `config/` | Runtime configuration | 🟡 Placeholder |
| Knowledge library | `knowledge_library/` | Reference knowledge | 🟡 Placeholder |
| Deployment | `deployment/` | VPS setup & ops | 🟡 Guide shell |
| Security | `security/` | Security policy | ✅ Baseline |

## 5. Runtime — NOT YET CHOSEN

The execution runtime (language + agent framework) is an **open owner decision**
(`OWNER_ACTION_REQUIRED.md`, Action 2). No agent code should be written until it's set.

Whatever is chosen must keep design goal #1 (portability): it must run on the owner's
PC, an external-drive copy, and a generic Linux VPS without code changes.

## 6. Data & secrets flow

```
Code  ──reads──▶  .env (local only, gitignored)  ──provides──▶  API keys/tokens
   │
   └──writes──▶  logs/ (gitignored)   memory/store/ (gitignored data)
```

- Code never contains secrets.
- `.env.example` documents which variables exist.
- `docs/api_keys_needed.md` tracks which keys are needed and when.

## 7. Portability contract

- One root folder: `sportsverse-os/`.
- Relative paths everywhere in code.
- No dependency that only works on one specific machine or one specific paid tool.
- Moving = copy the folder + recreate `.env`.

## 8. Open questions for the owner

- Tech stack / runtime (Action 2).
- Exact roles & permissions of Hermes and OpenClaw (`PROJECT_DNA.md` §6, §14).
- Brand structure (`PROJECT_DNA.md` §5).
- Which external services/APIs Sportsverse will actually use.
