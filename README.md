# Sportsverse OS

A portable, self-contained operating system of AI agents, workflows, and knowledge
for running the Sportsverse venture. Built to be **moved freely** between computers,
external drives, VPS servers, and different coding tools/agents without losing context.

> **New here? Read these five files in order:**
> 1. [`PROJECT_DNA.md`](PROJECT_DNA.md) — master identity & continuity
> 2. [`CURRENT_STATUS.md`](CURRENT_STATUS.md) — where we are right now
> 3. [`NEXT_STEPS.md`](NEXT_STEPS.md) — what to do next
> 4. [`reports/handoff/latest_handoff.md`](reports/handoff/latest_handoff.md) — last session handoff
> 5. This `README.md`

---

## Status

- **Project:** SportsVersusNews (sportsversenews.com) — see `config/project_context.json`
- **Phase:** 4 complete — Hermes Multi-Agent Operating Core (Jarvis + LangGraph + cost router + gates)
- **Last updated:** 2026-06-09
- **LLM:** **DeepSeek live and verified**; Nemotron optional (disabled); mock fallback intact.
- **Code:** Python + `openai` SDK (LangGraph + Nemotron optional). `python -m pytest` → 79 passing.
- **Safety:** Hermes is the final router; nothing publishes/spends/sends/installs without a gated approval; `execution_agent` takes no external action.

### Run it
```bash
cd sportsverse-os
python main.py                   # boot the agent org (no loops, nothing sent)
python -m pytest                 # run the test suite (pip install pytest if missing)
python scripts/smoke_review.py   # end-to-end gated owner-review demo (isolated; nothing published)
```

### Live AI drafts
Real drafts need ONE provider key in `.env` (already set to `LLM_MODE=live`). Paste a key on
the matching line (`ANTHROPIC_API_KEY` / `OPENAI_API_KEY` / `DEEPSEEK_API_KEY`), then install
that one SDK (`pip install anthropic` or `pip install openai`). No key → safe mock fallback.

### Review drafts (owner surface — four choices)
```bash
python -m review list                        # drafts waiting for review
python -m review show <id>                    # read a draft in full (incl. gates)
python -m review approve <id>                 # approve the DRAFT only        -> owner_approved
python -m review revise <id> --notes "..."    # request a revision (drafts a new version)
python -m review reject <id> --reason "..."   # archive with a reason         -> owner_rejected
python -m review schedule <id>                # approve for scheduled publish (6 gates) -> NOT published
```

### Schedule approved drafts (proposes times — never posts)
```bash
python -m scheduler propose                   # propose times for approved items
python -m scheduler list                      # show proposed/confirmed/cancelled slots
python -m scheduler confirm <slot_id>         # confirm a time (still does NOT post)
python -m scheduler cancel <slot_id> --reason "..."
```

### Phase 4 — the Hermes Operating Core (Jarvis)
```bash
python -m orchestration "research trending football stories"   # Jarvis -> Hermes -> agents
python scripts/smoke_phase4.py                                  # full core demo (mock, isolated)
python -m approval list                                         # gated-action approval queue
python -m approval approve <id> | reject <id> --reason "..."
```
Routing: DeepSeek for routine work; Nemotron (optional) for complex reasoning. Over-budget tasks
and gated actions (publish/email/spend/install/VPS/payment) require approval. Nothing posts.

---

## Folder Structure

```
sportsverse-os/
├─ README.md                 ← you are here
├─ PROJECT_DNA.md            ← master identity & continuity (read first)
├─ CURRENT_STATUS.md         ← live status snapshot
├─ NEXT_STEPS.md             ← next-agent instructions
├─ OWNER_ACTION_REQUIRED.md  ← things only the owner can do
├─ .env.example              ← template for secrets (copy to .env locally)
├─ .gitignore                ← keeps secrets/logs out of version control
│
├─ core/                    ← framework: paths, config, logging, llm_router, policy
│  └─ providers/           ← LLM providers: mock (default), openai, anthropic, deepseek
├─ agents/                  ← base + hermes / openclaw / sentinel / archivist / compliance
├─ skills/                  ← whitelist registry + draft-only skills
├─ review/                  ← owner-review surface + 6-gate automation (python -m review)
├─ scheduler/               ← proposes/confirms posting times — never posts (python -m scheduler)
├─ orchestration/           ← Phase 4 LangGraph core: state, journal, routes, app (python -m orchestration)
├─ providers/               ← cost-aware model router + DeepSeek/Nemotron adapters
├─ approval/                ← human-approval queue for gated actions (python -m approval)
├─ constitution/            ← system rules & approval rules
├─ architecture/            ← how the system is designed
├─ memory/                  ← memory manager + schema + stored memories/audit log
├─ knowledge_library/       ← reference knowledge for the system
├─ integrations/            ← external service connectors (later)
├─ workflows/               ← multi-step automations (later)
├─ config/                  ← configuration templates
├─ docs/                    ← documentation (incl. api_keys_needed.md)
├─ deployment/              ← VPS setup & deployment guides
├─ security/                ← security policy & practices
├─ reports/                 ← reports
│  └─ handoff/              ← session handoff notes (latest_handoff.md)
├─ logs/                    ← runtime logs (gitignored)
├─ tests/                   ← tests
└─ scripts/                 ← helper scripts
```

---

## Core Principles

1. **Portable** — everything lives under `sportsverse-os/`. Relative paths only. No machine-specific paths in code.
2. **Secret-safe** — secrets go in a local `.env` (never committed). Only `.env.example` is shared.
3. **Documented** — every major step is written down so a new agent/tool can continue.
4. **Low-cost** — prefer free/open-source/low-cost tools; avoid subscription stacking.
5. **Owner-in-the-loop** — agents never spend money, publish, or take binding actions without owner approval.

---

## Moving / Backing Up This Project

Because everything is under one folder, moving is simple:

- **To an external drive:** copy the whole `sportsverse-os/` folder.
- **To another computer:** copy the folder; recreate `.env` from `.env.example`.
- **To a VPS:** follow [`deployment/vps_setup_guide.md`](deployment/vps_setup_guide.md).
- **To a different coding agent/tool:** point it at this folder and have it read the five files above.

> ⚠️ Never copy a real `.env` to an untrusted location — it contains secrets.

---

## Getting Started (for a coding agent)

1. Read the five continuity files (top of this README).
2. Check `OWNER_ACTION_REQUIRED.md` for pending owner decisions (e.g. tech stack).
3. Follow `NEXT_STEPS.md`.
4. Stay within the current phase; document everything; update the handoff file when done.

## Getting Started (for the owner)

1. Open `OWNER_ACTION_REQUIRED.md` and complete any pending actions when you're ready.
2. Everything technical is handled by the coding agent — you only do what that file lists.
