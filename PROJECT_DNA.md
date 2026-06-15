# PROJECT_DNA.md

> **MASTER IDENTITY & CONTINUITY FILE**
> This is the single source of truth for the entire Sportsverse OS project.
> If you are a new coding agent, a new tool, or the owner returning after a break:
> **read this file first.** It tells you what this project is and how to continue it.
>
> **Update this file after every major coding session.**

---

## 0. How To Use This File

- Items marked **`[TBD — OWNER INPUT NEEDED]`** require a decision or fact only the owner can supply. Do not invent them.
- Items marked **`[SCAFFOLD]`** are reasonable defaults a coding agent set up; they can be changed freely.
- Items marked **`[LOCKED]`** are owner decisions that must not be changed without explicit owner approval.
- Dates are written in absolute form (e.g. `2026-06-08`), never "today" or "last week".

| Field | Value |
|---|---|
| Project name | Sportsverse OS |
| Root folder | `sportsverse-os` |
| Created | 2026-06-08 |
| Last DNA update | 2026-06-08 |
| Current phase | Phase 4 complete — Hermes Multi-Agent Operating Core (Jarvis + LangGraph + cost router + gates) |
| Project name | **SportsVersusNews** (sportsversusnews.com) — see §1a business context |
| Tech stack | Python 3.9+ + `openai` SDK (DeepSeek live); LangGraph + Nemotron optional `[LOCKED]` |
| LLM | **DeepSeek live and verified**; Nemotron optional (disabled); mock fallback intact |
| Document owner | Project Owner (Kamal) |

---

## 1. What Sportsverse Is

**Sportsverse** is the owner's parent sports brand. Its first active product is a
**faceless sports media channel** ("Platinum Clips") plus an **affiliate-intelligence**
operation that finds and tracks monetisation opportunities around sports content.

**Sportsverse OS** is the internal "operating system" that runs the venture: a
coordinated set of AI agents, workflows, integrations, memory, and knowledge that
help the owner operate Sportsverse with the leverage of a much larger team.

Sportsverse OS is **not** the product sold to customers — it is the internal control
system behind the Sportsverse brand(s).

---

## 1a. Business Context (SportsVersusNews)  `[LOCKED]`

| Field | Value |
|---|---|
| Project name | **SportsVersusNews** |
| Domain | sportsversusnews.com |
| Main email | sportsverseceo@gmail.com |
| Hosting | Hostinger |
| VPS | Hostinger VPS |
| Default LLM | DeepSeek API |
| Owner planning tool | ChatGPT Plus |
| Goal | A low-cost, AI-assisted sports/news business system with gated automation + human-in-the-loop |

(Stored in `config/project_context.json`. "SportsVersusNews" is the operating name; "Sportsverse"
was the earlier working title; "Platinum Clips" remains a possible media channel.)

## 2. The Business Mission

Build a portable, agent-driven operating system that lets one owner run the Sportsverse
sports-media brand (and future sub-brands) with the leverage of a much larger team —
cheaply, safely, and without lock-in to any single tool, computer, or vendor.

Locked guiding principles (see Section 12):
- **Portability over convenience** — movable to a drive, VPS, or different AI tool anytime.
- **Low cost over feature-stacking** — prefer free/open-source/low-cost tools.
- **Continuity over speed** — every major step is documented for handoff.
- **Human-in-the-loop** — no public posting without owner approval; DM/comment replies only from approved templates.

---

## 3. Active Phase

**Phase 4 — Hermes Multi-Agent Operating Core** *(complete on 2026-06-09)*

Phases 0–3 are complete and preserved. Phase 4 adds a Hermes-led multi-agent core. **Hermes is
the Executive Officer / supervisor and the final router.** No sub-agent may publish, spend, send
messages, install tools, or change production systems without a gated approval.

- **Jarvis** (`agents/jarvis.py`) — command interface (chat/CLI/voice-later). Converts requests
  into structured tasks and reports back in plain English. Makes NO executive decisions; hands to Hermes.
  CLI: `python -m orchestration "<request>"`.
- **LangGraph orchestration** (`orchestration/`) — a stateful graph with the 13 spec nodes
  (jarvis_input, hermes_router, cost_router, research/coding/content/compliance/openclaw/nemotron
  agents, human_approval_gate, execution_agent, memory_logger, final_report). Uses LangGraph when
  installed, else an identical built-in runner (zero extra deps).
- **Cost-aware model router** (`providers/model_router.py`) — **DeepSeek** for routine work;
  **Nemotron** only for complex reasoning/planning/architecture/high-value decisions (and only if
  enabled). Tracks tokens + cost per task; monthly budget + per-task threshold; over-budget tasks
  route to human approval BEFORE any spend. `config/model_budget.json`.
- **Nemotron/NeMo adapter** (`providers/nemotron_provider.py`) — pluggable (API / local / NIM);
  `NEMOTRON_ENABLED=false` by default → graceful fallback to DeepSeek. No hard-coded provider logic.
- **OpenClaw skill adapter** (`agents/openclaw_skill_agent.py`) — controlled, NOT an orchestrator.
  Allowlist `config/openclaw_allowlist.json`; all unapproved skills blocked by default; never
  secrets/keys/shell/db/payments; every invocation logged; security warning on unknown skills.
- **Human approval gates** (`approval/approval_queue.py`) — required before publishing, email,
  website changes, spending over threshold, installing skills, VPS/server config, public posts,
  payment/banking changes. `python -m approval list | approve | reject`.
- **Agent journal** (`logs/agent_journal.jsonl`, `orchestration/journal.py`) — structured log of
  every task (ts, request, route, model, est tokens, est cost, tools, approval status, final
  output). Hermes can review prior decisions (`Hermes.review_journal()`).

> **Safety invariants (LOCKED):** no autonomous publishing; no autonomous spend above threshold;
> no unapproved OpenClaw skills; no secrets in logs; no production action without approval. The
> `execution_agent` node performs NO production actions. Everything is modular so providers swap easily.

Carried forward & preserved: Phase 1–3 (skills, review surface `python -m review`, scheduler
`python -m scheduler`, Sentinel/Archivist/Compliance, live DeepSeek). All prior tests still pass.

---

## 4. Future Phases & Future Brands

**Phases** (scaffolded direction; owner confirms/edits):

| Phase | Name | Goal | Status |
|---|---|---|---|
| 0 | Portable Foundation | Portable folder + continuity system | ✅ Complete |
| 1 | Core Agent Framework | Agent runtime, base agent, services wiring | 🟡 Skeleton complete |
| 2 | First Real Agents | Implement Hermes orchestration + LLM router + first OpenClaw skills | Planned |
| 3 | Integrations | Telegram, email reports, sports data, web research | Planned |
| 4 | Workflows | Multi-agent automations (e.g. clip pipeline w/ compliance gate) | Planned |
| 5 | Deployment | Move to VPS, run continuously, backups | Planned |
| 6 | Scale & Brands | Expand to the future sub-brands below | Planned |

**Future brands under Sportsverse** (parent brand):
- **Sportsverse.fitness**
- **Sportsverse.gaming**
- **Sportsverse App**
- **Academy** — name `[TBD — OWNER INPUT NEEDED]`

These are future scope. Do not build brand-specific modules until Phase 6 / owner approval.

---

## 5. Brand Structure

```
Sportsverse (parent brand)
 ├─ Platinum Clips        — MAIN media channel (faceless sports media)  [ACTIVE]
 ├─ Affiliate Intelligence — monetisation research/tracking            [ACTIVE focus]
 ├─ Sportsverse.fitness   — future brand
 ├─ Sportsverse.gaming    — future brand
 ├─ Sportsverse App       — future product
 └─ Academy (name TBD)    — future brand
```

- **Active now:** Platinum Clips (faceless sports media) + affiliate intelligence.
- **Everything else:** future — scaffolded, not built.

---

## 6. Agent Structure

```
Owner (human, final authority)
 └─ Hermes — CEO / Orchestrator agent                         [reports to: Owner]
     ├─ OpenClaw — skill-execution layer (UNDER Hermes)       [reports to: Hermes]
     ├─ Sentinel — integrity / security / drift monitor       [reports to: Hermes]
     ├─ Archivist — institutional memory & handoff keeper      [reports to: Hermes]
     └─ Compliance Division — platform/copyright/fair-use/     [reports to: Hermes]
                              affiliate/FTC/brand-safety +
                              YouTube/TikTok/Instagram review
```

Roles `[LOCKED]`:
- **Hermes** — CEO/orchestrator. Plans and delegates; does not execute skills directly.
- **OpenClaw** — skill-execution layer **under** Hermes (never above). Executes concrete skills Hermes assigns.
- **Sentinel** — monitors integrity, security, and drift; reports issues up to Hermes.
- **Archivist** — keeps institutional memory and the handoff system current.
- **Compliance Division** — reviews anything public-facing across platform policy, copyright, fair use, affiliate rules, FTC disclosure, brand safety, and per-platform (YouTube/TikTok/Instagram) before publishing.

Each agent has a code skeleton in `agents/` and a place for a formal `agent.md` definition
(to be added when real behaviour is built). See `architecture/agent_architecture.md`.

### 6a. Skill Layer (whitelist, draft-only)

OpenClaw executes only **whitelisted, draft-only** skills from `skills/registry.py`. Each
skill declares: name, purpose, risk level, allowed actions, prohibited actions, and whether
human approval is required. The registry refuses to register any skill that is not
draft-only or that allows a forbidden action (publish/post/email/buy/upload/modify-code).

Initial six skills (all draft-only, all require human approval):
`sports_topic_research_draft`, `video_idea_draft`, `script_outline_draft`,
`affiliate_product_research_draft` (risk: medium), `compliance_review_draft`,
`daily_report_draft`.

They may create drafts/reports only. They may **not** publish, post, email externally,
buy, upload, or modify production code.

---

## 7. Current Architecture

**Tech stack:** Python 3.9+ `[LOCKED]` — chosen because the project needs AI agents,
memory, automation, Telegram, email reports, web-research workflows, future video tooling,
and VPS portability, all of which Python serves well with a large free/open-source ecosystem.

Code layout (all under `sportsverse-os/`):

```
core/         paths, config, logging, llm_router, policy
core/providers/  base, mock (default), openai, anthropic, deepseek
agents/       base.py + hermes / openclaw / sentinel / archivist / compliance
skills/       base, registry (whitelist), drafts (the 6 draft-only skills)
review/       owner-review surface + 6 gates  (`python -m review`)
scheduler/    proposes/confirms posting times; never posts  (`python -m scheduler`)
agents/       + jarvis, research/content/coding/compliance/openclaw_skill/nemotron_reasoning agents
orchestration/ state, journal, routes (13 nodes), langgraph_app  (`python -m orchestration "..."`)
providers/    deepseek_provider, nemotron_provider, model_router (cost-aware)
approval/     approval_queue + cli  (gated actions; `python -m approval`)
memory/       manager.py (file memory + event log + structured audit log) + store/
config/       settings + model_budget.json + openclaw_allowlist.json + project_context.json
tests/        pytest suite (85 passing)
main.py       boots the Phase 1–3 org; orchestration is the Phase 4 entry
```

**Phase 4 follow-up (2026-06-09):** Compliance deepened from "pending" stubs to real per-dimension
heuristics (`pass`/`warn`/`flag` + notes; any `flag` fails Gate 3; still never auto-approves). The
orchestration now feeds **content_agent** drafts that pass compliance into the owner-review queue
(`execution_agent` → `review/`), so a chat command flows: command → DeepSeek → compliance →
`python -m review` → `python -m scheduler`. Verified live end-to-end. All CLIs are UTF-8-safe.

Review data lives under `reports/review/` (`<id>.json` active, `archive/` rejected) and is
gitignored runtime data. The audit trail lives in `memory/store/audit-<date>.jsonl`.
Live secrets live ONLY in `.env` (gitignored); `LLM_MODE=live` enables real provider calls.

```
            OWNER (final authority, approvals)
               │
            Hermes  ── orchestrator
               │  delegates
     ┌─────────┼───────────────┬───────────────┐
  OpenClaw   Sentinel       Archivist      Compliance
  (skills)   (integrity)    (memory)       (gates publishing)
     │           │               │              │
     └─────┬─────┴───────┬───────┴──────────────┘
           ▼             ▼
     LLM Router     Memory (file-based)   +   Integrations (Telegram/email, dry-run)
```

Architecture principles `[LOCKED]`:
- **Portable** — relative paths via `core/paths.py`; no machine-specific absolute paths.
- **Secret-safe** — secrets only in local `.env`; never committed; never logged.
- **Documented** — every module has a docstring/README.
- **Safe by default** — publishing requires human approval; integrations default to dry-run; DM replies are template-only.

---

## 8. Current Build Progress

| Area | Status |
|---|---|
| Folder structure | ✅ Complete |
| Continuity files (DNA/status/next/owner/README) | ✅ Complete |
| Constitution + approval rules | ✅ Complete |
| Architecture + memory schema docs | ✅ Complete |
| Handoff system | ✅ Complete |
| `.env.example` + `.gitignore` + `docs/api_keys_needed.md` | ✅ Complete |
| VPS deployment guide shell | ✅ Complete |
| **Python package structure** | ✅ Complete (Phase 1) |
| **Agent base class** | ✅ Skeleton |
| **Hermes / OpenClaw / Sentinel / Archivist / Compliance** | ✅ Skeletons |
| **LLM router** | ✅ Skeleton (no network) |
| **Memory manager** | ✅ Functional (file-based, basic) |
| **Telegram + email integrations** | ✅ Skeletons (dry-run, never send) |
| **Workflow runner** | ✅ Skeleton (approval gate works) |
| **Config loader + logging** | ✅ Functional |
| **LLM router + provider abstraction** | ✅ Mock default; openai/anthropic/deepseek wired (Phase 2A) |
| **Hermes→OpenClaw delegation** | ✅ Classify → Sentinel → OpenClaw → Compliance (Phase 2A) |
| **Skill registry + 6 draft-only skills** | ✅ Whitelisted (Phase 2A) |
| **Sentinel skill-permission review** | ✅ Blocks high-risk; logs to memory (Phase 2A) |
| **Compliance risk scoring** | ✅ `review_draft` risk score + notes (Phase 2A) |
| **Memory audit log** | ✅ `log_event` / `read_events` (Phase 2A) |
| **Owner-review surface** | ✅ Queue + CLI; approve/reject/revise; memory-logged (Phase 2B) |
| **Live LLM (auto-detect + mock fallback)** | ✅ anthropic/openai/deepseek; safe fallback (Phase 2C) |
| **6-gate scheduled-publish automation** | ✅ `review/automation.py` (Phase 2C) |
| **Full status lifecycle (8 statuses)** | ✅ draft_created → … → approved_for_scheduled_publish (Phase 2C) |
| **Structured audit log** | ✅ `log_audit` with all required fields (Phase 2C) |
| **Live DeepSeek LLM** | ✅ Connected + verified end-to-end (`is_mock=False`) (2026-06-09) |
| **Scheduler (propose/confirm/cancel times)** | ✅ `scheduler/` + `python -m scheduler` (Phase 3) |
| **Jarvis interface + LangGraph core (13 nodes)** | ✅ `orchestration/` (Phase 4; langgraph optional) |
| **Cost-aware model router (DeepSeek/Nemotron)** | ✅ `providers/model_router.py` + budget gating (Phase 4) |
| **Nemotron adapter (optional, fallback to DeepSeek)** | ✅ `providers/nemotron_provider.py` (Phase 4) |
| **OpenClaw allowlist skill adapter** | ✅ `agents/openclaw_skill_agent.py` + allowlist (Phase 4) |
| **Human approval gates + queue** | ✅ `approval/` + `python -m approval` (Phase 4) |
| **Agent journal (structured per-task log)** | ✅ `logs/agent_journal.jsonl` (Phase 4) |
| **Deepened Compliance (per-dimension pass/warn/flag)** | ✅ real heuristics; any flag fails Gate 3 (Phase 4 follow-up) |
| **Orchestration → review queue wiring** | ✅ content drafts flow into `python -m review` (Phase 4 follow-up) |
| **Approve/schedule/execute all != publish** | ✅ `published` always False; execution_agent does nothing external |
| **Tests** | ✅ 85 passing (`pytest`) |
| boot + review/scheduler/approval/orchestration CLIs + smokes + live | ✅ All run clean |
| Any publish/post execution (real platform APIs) | ⛔ Not built (intentionally; future, owner-gated) |

---

## 9. What Has Already Been Completed

As of `2026-06-08`:
- **Phase 0:** full portable folder + continuity/handoff/secret-safety system.
- **Phase 1 skeleton:** Python framework — base agent, five agent skeletons, file-based
  memory manager, config loader, logging, Telegram/email dry-run integrations, workflow
  runner with a human-approval gate, `main.py` boot.
- **Phase 2A:** provider-abstracted LLM router (mock default; openai/anthropic/deepseek);
  Hermes NL classification + delegation pipeline; whitelist skill registry + six draft-only
  skills; Sentinel skill-permission review (blocks high-risk, logs to memory); Compliance
  risk scoring (`review_draft`); memory event audit log.
- **Phase 2B:** owner-review surface (`review/`): file-based review queue + CLI; approve,
  reject, request revision; all actions logged; Hermes auto-submits finished drafts.
- **Phase 2C:** live LLM support (provider auto-detect + safe mock fallback); six-gate
  scheduled-publish automation; full 8-status lifecycle; fourth owner action; structured audit log.
- **DeepSeek activation (2026-06-09):** owner chose DeepSeek; `openai` SDK installed;
  `.env` `LLM_MODE=live` + `LLM_PROVIDER=deepseek` + key. **Verified live**: `check_live_llm.py`
  returned a real response (`is_mock=False`); a real draft ran the full pipeline (risk 25/100, queued).
- **Phase 3 (scheduler):** `scheduler/` proposes/confirms/cancels times for
  `approved_for_scheduled_publish` items; CLI `python -m scheduler`; audit-logged; **never posts**.
- **Phase 4 (Hermes operating core):** Jarvis interface; LangGraph orchestration (13 nodes,
  langgraph-or-fallback); cost-aware model router (DeepSeek default, optional Nemotron, budget
  gating); OpenClaw allowlist adapter; human-approval queue + gated actions; agent journal.
  Business context set to **SportsVersusNews**.
- Verified: `pytest` → **79 passing**; `smoke_phase4.py` shows routing + gates + allowlist +
  journaling with `any_published=False`; a **live** orchestrated task ran through the whole core
  via `python -m orchestration` (real DeepSeek, `is_mock=false`, `completed_no_external_action`).

No content is published anywhere. Live calls use the owner's DeepSeek key in `.env`.

---

## 10. What Still Needs To Be Built

In priority order (authoritative list in `NEXT_STEPS.md`):
1. **Optionally enable LangGraph** (`pip install langgraph`) and/or **Nemotron** (set the
   `NEMOTRON_*` env vars) — both are auto-detected; no code change needed.
2. **Deepen Compliance checks** (optionally DeepSeek-assisted); still human-gated; never auto-approve.
3. **Phase 5 — Publisher (future, strictly owner-gated):** ONLY here are real platform APIs
   (YouTube/TikTok/Instagram/Telegram/email/website) added, behind explicit per-item owner approval.
   This is the only place a gated action is actually executed. Do NOT start without owner instruction.
4. Connect the orchestration output to the review/scheduler queues; agent.md definitions; HTML views.
5. VPS deployment to the Hostinger VPS (see `deployment/vps_setup_guide.md`).

Still explicitly OUT until the owner says otherwise: any publish step, auto-posting,
buying/uploading anything. Even `approved_for_scheduled_publish` is NOT published — a separate,
owner-gated publishing step is a future phase requiring explicit per-item approval.

---

## 11. Key Owner Decisions

| Date | Decision | Notes |
|---|---|---|
| 2026-06-08 | Project must be fully portable | `[LOCKED]` |
| 2026-06-08 | All files under one root: `sportsverse-os/` | `[LOCKED]` |
| 2026-06-08 | Prefer local/open-source/low-cost tools; avoid subscription stacking | `[LOCKED]` |
| 2026-06-08 | No real secrets in code; use `.env` + `.env.example` | `[LOCKED]` |
| 2026-06-08 | Build foundation before agents | `[LOCKED]` |
| 2026-06-08 | **Tech stack = Python** | `[LOCKED]` |
| 2026-06-08 | Parent brand = Sportsverse; main channel = Platinum Clips; focus = faceless sports media + affiliate intelligence | `[LOCKED]` |
| 2026-06-08 | Agents: Hermes (CEO), OpenClaw (skills, under Hermes), Sentinel, Archivist, Compliance | `[LOCKED]` |
| 2026-06-08 | **Human approval required before public posting** | `[LOCKED]` |
| 2026-06-08 | **DM/comment replies only from approved templates** | `[LOCKED]` |
| 2026-06-08 | LLM providers supported: OpenAI, Anthropic, DeepSeek; **mock is the default** | `[LOCKED]` |
| 2026-06-08 | Skills are **whitelist-only and draft-only**; high-risk blocked by default | `[LOCKED]` |
| 2026-06-08 | **Approval is not publishing** — and **scheduling is not publishing** (`published` always False) | `[LOCKED]` |
| 2026-06-08 | Owner reviews via `python -m review` (approve / revise / reject / schedule) | `[LOCKED]` |
| 2026-06-08 | Live LLM via `.env` `LLM_MODE=live`; router **auto-detects** the one key present; **mock fallback** on any failure | `[LOCKED]` |
| 2026-06-08 | **6 gates** required before `approved_for_scheduled_publish`; Gate 3 = compliance risk < threshold (50) | `[LOCKED]` |
| 2026-06-08 | Every action audited (ts, draft id, action, agent, owner decision, compliance score, final status) | `[LOCKED]` |
| 2026-06-09 | **LLM provider = DeepSeek** (OpenAI-compatible, `openai` SDK). **Live verified** (`is_mock=False`). | `[LOCKED]` |
| 2026-06-09 | **Scheduling is not publishing** — a `confirmed` slot is a plan only; `published` stays False | `[LOCKED]` |
| 2026-06-09 | Owner schedules via `python -m scheduler` (propose / confirm / cancel); default cadence 1/day @ 17:00 | `[LOCKED]` |
| 2026-06-09 | Project operating name = **SportsVersusNews** (sportsversusnews.com, Hostinger VPS) | `[LOCKED]` |
| 2026-06-09 | **Hermes is the Executive Officer / final router**; OpenClaw is a controlled skill adapter, never the orchestrator | `[LOCKED]` |
| 2026-06-09 | Model routing: **DeepSeek default**, **Nemotron** only for complex work (optional, fallback DeepSeek) | `[LOCKED]` |
| 2026-06-09 | LangGraph + Nemotron are **optional** (auto-detected); built-in fallback keeps it dependency-free | `[LOCKED]` |
| 2026-06-09 | Over-budget tasks (per-task threshold / monthly budget) route to human approval **before** spend | `[LOCKED]` |
| 2026-06-09 | 8 gated actions always need approval (publish, email, website, spend>threshold, install skill, VPS, public post, payments) | `[LOCKED]` |
| _next_ | First LLM provider + key + switch to `LLM_MODE=live` (Anthropic/OpenAI/DeepSeek) | `[TBD]` |
| _next_ | Academy brand name | `[TBD]` |

---

## 12. System Rules

(Full version in `constitution/constitution.md`.)

1. Stay portable — relative paths, one root folder, no scattering.
2. Never hard-code secrets — use `.env`; commit only `.env.example`; never log secrets.
3. Document every major step inside the project folder.
4. Update continuity files after each major session.
5. Do all work that doesn't require the owner; only escalate per the Approval Rules.
6. Prefer cheap/open-source tools; avoid unnecessary paid subscriptions.
7. Never build future-phase modules early without owner approval.
8. Keep agents within their defined permissions.
9. **No public posting without human approval; DM/comment replies only from approved templates.**

---

## 13. Approval Rules

A coding agent must **stop and ask the owner** only when:
- An account must be created.
- A paid tool / paid plan decision is required.
- An API key or secret is needed.
- A legal or business decision is required.
- A security-sensitive choice is needed.
- Multiple viable tools exist and the best choice is not obvious.

Document options/trade-offs in `OWNER_ACTION_REQUIRED.md` and let the owner decide
(owner may consult ChatGPT first). Everything else: proceed autonomously and document.

---

## 14. OpenClaw Position Under Hermes

`[LOCKED]` — **OpenClaw is the skill-execution layer UNDER Hermes — never above it.**
Hermes (CEO/orchestrator) decides *what* to do and delegates; OpenClaw *executes* the
concrete skills it is assigned, within policy.

- OpenClaw only runs skills delegated by Hermes.
- OpenClaw escalates to Hermes anything ambiguous or matching the Approval Rules.
- OpenClaw must never publish externally or send a non-template reply on its own — those require human approval.

Implemented as `agents/openclaw.py` with a skill registry (no production skills yet).

---

## 15. Compliance Rules

The **Compliance Division** (`agents/compliance.py`) reviews anything public-facing across:
**platform policy, copyright, fair use, affiliate rules, FTC disclosure, brand safety,**
and **per-platform review for YouTube / TikTok / Instagram**.

Phase 1 behaviour: every check returns "pending" and the overall verdict is
`needs_human_review` — i.e. nothing is auto-approved for posting. This enforces the
locked rule: **human approval required before public posting.**

Baseline compliance rules (also in `constitution/constitution.md` and `security/security_policy.md`):
- Never store/commit/log real secrets.
- Respect every platform's terms of service and rate limits.
- Only use sports data/media/content the owner has the right to use.
- Outbound communication must comply with disclosure/anti-spam rules and platform policy.
- DM/comment replies only from approved templates.

`[TBD — OWNER INPUT NEEDED]` — Confirm legal jurisdiction(s) whose rules apply.

---

## 16. Handoff Instructions

To hand off:
1. Update `reports/handoff/latest_handoff.md`.
2. Update `CURRENT_STATUS.md`, `NEXT_STEPS.md`, and this file's Sections 8–11.
3. Ensure no real secrets are committed (only `.env.example`).
4. Copy the entire `sportsverse-os/` folder. Nothing critical lives outside it.

To **receive** a handoff, read in this order:
1. `PROJECT_DNA.md` (this file) → 2. `CURRENT_STATUS.md` → 3. `NEXT_STEPS.md`
→ 4. `reports/handoff/latest_handoff.md` → 5. `README.md`.

---

## 17. How Another Coding Agent Should Continue

1. **Read the five continuity files** (Section 16).
2. **Stack is Python.** Run `python main.py` to boot; `pytest` to test. Don't re-pick the stack.
3. **Respect the phase.** Phase 1 skeleton is done; Phase 2 = put real behaviour inside the skeletons. Don't jump to deployment/brands.
4. **Stay portable & safe** — relative paths, `.env` secrets, no public posting without approval, integrations stay dry-run until explicitly enabled.
5. **Follow the Approval Rules** (Section 13).
6. **Document as you go** and update Sections 8–11 + the handoff file at session end.
7. **Never change `[LOCKED]` decisions** without explicit owner approval.

---

_End of PROJECT_DNA.md_
