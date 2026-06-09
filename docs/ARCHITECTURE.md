# SportVerse Labs — System Architecture

**Business:** SportVerse Labs · **Brand:** SportsVersusNews · **Domain:** sportsversusnews.com
**Executive agent:** Hermes · **Command layer:** Jarvis · **Default model:** DeepSeek · **Engine:** LangGraph (optional, fallback built-in)

---

## 1. Layers

```
                 OWNER (Telegram / CLI / Dashboard)
                            │
                  ┌─────────▼─────────┐
                  │  Jarvis (interface)│  parses commands → structured tasks; reports plainly
                  └─────────┬─────────┘
                  ┌─────────▼─────────┐
                  │ Hermes (Executive)│  routes by type/risk/cost; final decision-maker
                  └─────────┬─────────┘
        ┌──────────────────┼─────────────────────────────┐
        ▼                  ▼                              ▼
  Cost router        Worker agents                   Compliance
  (DeepSeek/         research / content / video /     (policy/copyright/
   Nemotron,         coding / nemotron-reasoning /     fair-use/FTC/brand
   budget gate)      openclaw-skill                    /per-platform)
        │                  │                              │
        └────────┬─────────┴───────────┬──────────────────┘
                 ▼                      ▼
        Human-approval gate     Owner-review queue ──► Scheduler (proposes times)
        (publish/spend/etc.)    (draft→review→schedule)        │
                 │                                             ▼
                 └────────────► Agent journal + audit log ◄────┘
```

Operations agents wrap around this: **security**, **deployment**, **github_backup**,
**dns_website**, **dashboard**, **documentation**, **analytics**, **approval**, **social_publishing**.

## 2. Data flow (a content command)
1. Owner: `python -m orchestration "draft a caption ..."` (or Telegram).
2. Jarvis → structured task → Hermes routes → cost router picks DeepSeek (or Nemotron if complex+enabled).
3. Worker drafts → Compliance scores → if it passes and is content, it's queued into the **review** surface.
4. Owner reviews (`python -m review` / Telegram `/approve`) → approves for scheduling → **scheduler** proposes a time.
5. Nothing posts. Publishing is a future, per-item, owner-approved Phase 5 capability.

## 3. Safety invariants
- Hermes is the final router; no sub-agent publishes/spends/sends/installs/changes production without a gated approval.
- `execution_agent` performs NO external action.
- Over-budget tasks (per-task threshold / monthly cap in `config/model_budget.json`) pause for approval **before** spend.
- OpenClaw runs allowlisted skills only (`config/openclaw_allowlist.json`); unknown skills blocked + security warning.
- Secrets live only in `.env` (gitignored); never logged, never committed.

## 4. Key directories
`agents/`, `orchestration/`, `providers/`, `approval/`, `review/`, `scheduler/`, `reporting/`,
`integrations/` (Telegram), `dashboard/`, `skills/`, `memory/`, `config/`, `scripts/`, `docs/`.

See `docs/AGENT_DIRECTORY.md` for each agent and `docs/DEPLOYMENT_GUIDE.md` to deploy.
