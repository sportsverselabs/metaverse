# Latest Handoff

> The baton-pass file. A new coding agent should be able to read this and continue
> with zero re-explanation from the owner. Newest session on top.
> Keep older handoffs by copying this to `handoff_YYYY-MM-DD.md` before major rewrites.

---

## Session: 2026-07-01 (k) — Dashboard workflow debug: render / thumbnail / pipeline-approval

**Agent:** Claude Code (Opus 4.8). **Goal:** fix owner-reported Creative Studio + Approvals issues.

### Root causes + fixes
- **Render "ffmpeg exited 254":** demo project referenced `assets/clip1.mp4` (relative, **missing**); the
  UI showed ffmpeg's *version banner* because stderr was truncated from the front. Fix: `preflight()` in
  `creative/providers/ffmpeg_editor.py` validates inputs-exist / output-writable / valid-trim / ffmpeg-
  installed **before** running; `_error_summary()` strips the banner and shows the real stderr tail; full
  detail logged (`creative.ffmpeg`). Demo now **generates a real sample clip** (ffmpeg lavfi) so it renders.
- **Thumbnail "generated" but invisible:** saved to `.../assets/thumbnail.png` but preview looked in the
  project **root**. Fix: save thumbnail at project root (`reports/video/<id>/thumbnail.png`); existence
  re-checked; editor shows a **Files & status** debug block + Refresh button.
- **Pipeline 0 while Approvals showed gated actions:** the 3 `publish_content` actions came from
  research_agent tasks that never produced a review draft → **orphaned** (approval queue and review store
  are separate). Fix: `review/reconcile.py` cross-checks actions vs review records; dashboard flags orphans
  "needs repair"; pipeline shows gated-action + orphan counts; `python -m review reconcile --apply` (and
  `scripts/reconcile_approvals.py`) safely reject orphans (reversible). Cleared the 3 real orphans on the VPS.

### Tests + smoke
- 8 new offline tests (`tests/test_dashboard_workflow.py`) + updated `test_creative.py`. `python -m pytest`
  → **184 passing**. `scripts/smoke_studio.py` on the VPS → **ALL PASS**: demo → render → thumbnail →
  files exist → previews show → no orphans → nothing published.

### Docs updated
`CURRENT_STATUS.md`, `NEXT_STEPS.md`, `PROJECT_DNA.md`, `README.md`, this handoff.

---

## Session: 2026-06-30 (j) — Hermes sports routing: sport scoping + fallback ideas

**Agent:** Claude Code (Opus 4.8)
**Goal:** Fix "make me 3 soccer video highlights" returning "no soccer games" when the live hub only had
MLB/NFL. **No live games must not mean no content ideas.**

### What changed
- `sports/context.py`: added **sport detection** (`detect_sport`/`sport_scope`) — "soccer" now maps to
  Premier League + MLS + API-Football (previously unrecognized → fell back to MLB/NFL). Added
  `research_basis()` and `highlight_ideas()` with a **fallback chain**: live → upcoming → recent results →
  recent news → **trending topics** → **evergreen concepts**. Every idea is tagged with a **basis**
  (`live-data` / `recent-news` / `trending-topic` / `evergreen`). Live data is preferred; trending/evergreen
  carry NO scores or events (nothing invented). `brief()` now emits a basis-labeled idea scaffold for
  idea/highlight requests and instructs the model "do not invent scores, quotes, players, or events."
- `sports/hub.py`: added `completed_games()` (final scores = real, from the scoreboard).
- Idea requests are NOT data-queries → they stay on the gated content path (compliance runs, nothing publishes).

### Tests (added to `tests/test_sports.py`)
- soccer request with no live data still returns 3 valid soccer ideas; no invented scores; basis marked on
  each idea + in the brief; live preferred when available; routing stays on the gated content path.
- `python -m pytest` → **174 passing**. Verified live: "make me 3 soccer video highlights" → 3 real soccer
  ideas (PL/MLS fixtures), not MLB/NFL.

### Docs updated
`docs/SPORTS_DATA_HUB.md` (sport scoping + fallback section), this handoff.

---

## Session: 2026-06-28 (audit) — Endpoint audit + Creative Studio plan (DOCS ONLY)

**Agent:** Claude Code (Opus 4.8)
**Goal:** Compare the build against the full Sportsverse OS endpoint vision; plan a dashboard-native
creative (video + thumbnail) studio. **No major features built** (per instruction — audit/plan only).

### What was produced
- **`architecture/MASTER_ENDPOINT_RUBRIC.md`** — the 30-item endpoint vision with honest per-item status
  (Built / Partial / Not built / Refactor / Blocked-owner / Blocked-external). ~55–60% of the vision built.
- **`architecture/CREATIVE_STUDIO_PLAN.md`** — dashboard-native video/thumbnail editor design.
  Open-source/local-first: **FFmpeg + MoviePy** render, **Pillow/SVG** thumbnails, browser clip-list
  editor, captions via SRT+FFmpeg burn (Whisper optional later), Remotion/FFmpeg.wasm deferred to V2.
  Provider interfaces: VideoEditorProvider / ThumbnailProvider / CaptionProvider. `VideoProject` JSON
  model + edit history. V1a (local render) → V1b (Studio UI) → V1c (AI revision + compliance loop).
- **`architecture/DEPARTMENT_SKILL_MAP.md`** — departments → Hermes roles → **reusable skill packs**
  (not random GitHub skills); the existing 6 draft skills become the seed packs.
- **`architecture/PLUGIN_PROVIDER_MAP.md`** — provider interfaces + cost order; LLM + Publishing exist
  as the blueprint; video/thumbnail/caption/research providers are the new local-first additions.
- **`architecture/BUILD_GAP_ANALYSIS.md`** — built / partial / missing / next / refactors / recommended
  next phase (Phase 6 Creative Studio) + blockers.

### Key findings
- Solid: operating core, Sports Data Hub, review/gates, dashboard, deploy, publishing (code).
- Biggest gap: **creative/video production surface** (video_agent is metadata-only; Video Review is a
  placeholder). Several "departments" (Creative, Marketing, Community, Commerce, Tech Scout) and the
  Knowledge Library are not built; skills aren't organized into packs.
- **Architecture supports dashboard-native video editing additively (no rewrite)** — the only hard
  external requirement is FFmpeg on the VPS (free).
- DeepSeek stays the default LLM behind provider abstraction; no paid-tool lock-in.

### Tests
No code changed → suite unchanged at **134 passing** (verified at session start).

### Recommended next phase
**Phase 6 — Dashboard-native Creative Studio**, plan-first then build **V1a** (local FFmpeg/Pillow render
foundation with offline tests). All safety rules carried forward (no auto-publish; edited content re-runs
compliance; no unapproved skills; no secrets in logs; no paid lock-in; decisions logged).

### Continuity files updated
`PROJECT_DNA.md`, `CURRENT_STATUS.md`, `NEXT_STEPS.md`, `README.md`, and this handoff.

---

## Session: 2026-06-09 (i) — Phase 4 follow-ups: deeper Compliance + review wiring

**Agent:** Claude Code (Opus 4.8)
**Goal:** "continue build" → the next safe NEXT_STEPS items (deepen Compliance; wire orchestration
output into the review queue). Phase 5 (real publishing) intentionally NOT started.

### What was built
- **Deepened Compliance** (`agents/compliance.py`): replaced "pending" stubs with real per-dimension
  heuristics returning `pass`/`warn`/`flag` + notes for platform_policy, copyright, fair_use,
  affiliate_disclosure, ftc_disclosure, brand_safety, and YouTube/TikTok/Instagram review. Risk
  score 0–100. **Gate 3 `passed` now requires risk < threshold AND no `flag`** (warn is advisory).
  Still never auto-approves (verdict always `needs_human_review`). Added optional, off-by-default
  `llm_assist` hook for a future DeepSeek second opinion.
- **Orchestration → review queue wiring**: `execution_agent` now queues `content_agent` drafts
  that pass compliance into the Phase 2 review surface (`SUBMIT_TO_REVIEW_ROUTES` in
  `orchestration/routes.py`; `GraphContext.review_store`; `build_services` wires a real ReviewStore;
  `OrchestrationState.review_id`). So a chat command flows: command → DeepSeek → compliance →
  `python -m review` → `python -m scheduler`. Internal-only routes (research/coding) are NOT queued.
- **UTF-8-safe CLIs** (`core/console.py` + applied to review/scheduler/approval/orchestration mains)
  so real model output (emojis, em-dashes) prints on Windows cp1252 consoles.

### Files
Created: `core/console.py`. Edited: `agents/compliance.py`, `orchestration/routes.py`,
`orchestration/state.py`, `orchestration/langgraph_app.py`, `agents/jarvis.py`,
`review/cli.py`, `scheduler/cli.py`, `approval/cli.py`, `orchestration/__main__.py`,
`tests/_phase4_helpers.py`, `tests/test_compliance.py`, `tests/test_phase4_graph.py`, docs.

### What was tested (results)
- `python -m pytest` → **85 passed** (79 + 6 new: 4 compliance dimensions, 2 review-wiring).
  Caught + fixed a design issue (non-critical flags must fail Gate 3).
- **Live**: `python -m orchestration "draft a hype caption ..."` → content_agent → DeepSeek (real
  caption w/ emojis) → compliance risk 0 → **queued as a review item**; `python -m review list`
  shows it (UTF-8 fix verified, exit 0).

### Known bugs
- None.

### Current phase
Phase 4 + follow-ups — **complete.** Next: optional LangGraph/Nemotron enablement; per-platform
compliance refinement; broaden review-queue feeding. Phase 5 (real publisher) LOCKED until owner asks.

### Owner action needed
- None. Optional: `python -m orchestration "..."`; review queued drafts via `python -m review`.

---

## Session: 2026-06-09 (h) — Phase 4: Hermes Multi-Agent Operating Core

**Agent:** Claude Code (Opus 4.8)
**Phase:** 4 — Jarvis + LangGraph orchestration + cost-aware model router + OpenClaw allowlist +
approval gates + agent journal. Business context set to **SportsVersusNews**.

### Design decisions (important for the next agent)
- **LangGraph and Nemotron are OPTIONAL with graceful fallback** (matching the project's existing
  patterns and portability rules). The SAME 13-node graph runs via a built-in runner when
  `langgraph` isn't installed; Nemotron falls back to DeepSeek when disabled. This keeps the
  system dependency-free and 100% offline-testable. `pip install langgraph` / set `NEMOTRON_*`
  to use the real engines (auto-detected). No heavy deps were force-installed.
- **Hermes is the Executive Officer / final router.** Sub-agents cannot publish/spend/send/
  install/change production. `execution_agent` performs NO external action — gated actions become
  pending approvals.
- New top-level `providers/` reuses `core.providers` base classes (no duplication).

### What was built (files)
- **providers/**: `__init__`, `deepseek_provider` (re-export), `nemotron_provider`, `model_router`
  (DeepSeek default / Nemotron-for-complex, token+cost estimate, monthly budget + per-task
  threshold → approval before spend, mock no-spend, CostTracker).
- **orchestration/**: `state` (OrchestrationState), `journal` (AgentJournal → logs/agent_journal.jsonl),
  `routes` (13 node fns + GraphContext + built-in runner), `langgraph_app` (build_services,
  build_langgraph_app, run_task, engine auto-detect), `__init__`, `__main__` (Jarvis CLI).
- **approval/**: `approval_queue` (GATED_ACTIONS, detect_gated_actions, ApprovalQueue), `cli`, `__main__`.
- **agents/**: `jarvis`, `worker_base`, `research_agent`, `content_agent`, `coding_agent`,
  `compliance_agent`, `openclaw_skill_agent` (allowlist), `nemotron_reasoning_agent`; updated
  `hermes.py` (route_task / decide / review_journal — existing Phase 2-3 pipeline preserved).
- **config/**: `model_budget.json`, `openclaw_allowlist.json`, `project_context.json`.
- **tests/**: `_phase4_helpers` + `test_phase4_{providers,cost,openclaw,routing,approval,graph}.py`.
- **scripts/smoke_phase4.py**; `logs/agent_journal.jsonl`; `reports/approvals/.gitkeep`.
- Edited: `core/paths.py` (APPROVALS_DIR, AGENT_JOURNAL, MODEL_BUDGET_FILE, OPENCLAW_ALLOWLIST_FILE),
  `.env`/`.env.example` (NEMOTRON_*), `.gitignore`, `requirements.txt`, docs.

### What was tested (results)
- `python -m pytest` → **79 passed** (52 prior + 27 Phase 4). New tests: DeepSeek default routing;
  Nemotron fallback when disabled + selection when enabled; cost tracking + over-threshold/monthly
  → approval without spend; OpenClaw allowlist blocking + security warning + audit; Hermes routing
  + Jarvis classification; gated-action detection + approval queue + orchestration pending (no exec);
  graph state transitions (exact node path) + journal logging + nothing published.
- `python scripts/smoke_phase4.py` → 6 scenarios incl. gated approval + blocked skill; `any_published=False`.
- **Live**: `python -m orchestration "research ..."` → real DeepSeek through the whole core,
  `is_mock=false`, `completed_no_external_action`, journal written. (Fixed a Windows cp1252 print
  crash by reconfiguring stdout to utf-8 in the Jarvis CLI.)

### Known bugs
- None. Real Nemotron/LangGraph paths are exercised only when enabled/installed (guarded + fallback).

### Current phase
Phase 4 — **complete.** Next: deepen Compliance; optionally enable LangGraph/Nemotron; wire
orchestration output into the review/scheduler queues. Phase 5 (real publisher) LOCKED until owner asks.

### Owner action needed
- None. Optional: try `python -m orchestration "..."`; `python -m approval list`; enable
  LangGraph (`pip install langgraph`) / Nemotron (`NEMOTRON_*` env) if desired.

### How to run
```bash
cd sportsverse-os
python -m pytest
python scripts/smoke_phase4.py
python -m orchestration "research trending football stories"
python -m approval list
```

---

## Session: 2026-06-09 (g) — DeepSeek live CONFIRMED + Phase 3 Scheduler

**Agent:** Claude Code (Opus 4.8)
**Goal:** Owner pasted the DeepSeek key ("do the rest"). Verify live; build Phase 3 scheduler.

### What was completed
- **Live DeepSeek verified end-to-end.** `check_live_llm.py` → real reply, `is_mock=False`,
  "SUCCESS". A real draft ran the full pipeline (Sentinel → OpenClaw → DeepSeek → Compliance →
  review queue): `is_mock=False`, risk **25/100** (passed), `published=False`, queued as
  `rv-2026-06-09-932b1b07` (left in the queue for the owner to review).
- **Phase 3 — Scheduler** (`scheduler/`): proposes times for `approved_for_scheduled_publish`
  items, owner confirms/cancels. Slot statuses proposed→confirmed/cancelled. CLI
  `python -m scheduler propose|list|confirm|cancel`. Audit-logged. **Never posts** — a confirmed
  slot is only a plan for a future Phase 4 publisher. No `publish`/`post` method anywhere.
- Wired `scheduler_store` into `build_system`; boot banner now "Phase 3 boot" + scheduler line.

### Files created
`scheduler/{__init__,models,planner,store,service,cli,__main__}.py`; `tests/test_scheduler.py`;
`scripts/smoke_scheduler.py`; `reports/schedule/.gitkeep`.
(Earlier this session: `scripts/check_live_llm.py`.)

### Files edited
`core/paths.py` (SCHEDULE_DIR), `main.py` (wire scheduler + banner), `.gitignore`
(reports/schedule), `requirements.txt` (openai), `.env` (LLM_PROVIDER=deepseek; owner added key),
and docs: PROJECT_DNA, CURRENT_STATUS, NEXT_STEPS, OWNER_ACTION_REQUIRED, README.

### What was tested (results)
- `python -m pytest` → **52 passed** (44 + 8 scheduler). New scheduler tests prove: planner
  assigns future spaced times; only `approved_for_scheduled_publish` items are scheduled; propose
  is idempotent; confirm→confirmed (published False); cancel→cancelled; **no publish method /
  nothing published**; actions audited; missing slot raises.
- `python scripts/check_live_llm.py` → live DeepSeek SUCCESS.
- Real pipeline draft via DeepSeek → real content queued, nothing published.
- `python scripts/smoke_scheduler.py` → approve→propose→confirm, `any_published=False`.

### What failed
- Nothing. (Fixed a sloppy `store.update` return early.)

### Known bugs
- None. Live calls use the owner's DeepSeek key in `.env` (gitignored).

### Current architecture
Adds `scheduler/` after the review queue. Flow: NL → Sentinel → OpenClaw → DeepSeek → Compliance
→ review (approve/revise/reject/schedule) → scheduler (propose/confirm/cancel times). No posting
exists; `published` is always False. Live LLM = DeepSeek via `openai` SDK + mock fallback.

### Current phase
Phase 3 — **complete.** Next: deepen Compliance checks. Phase 4 (real publisher) is LOCKED until
the owner explicitly asks.

### Next recommended task
1. Deepen Compliance checks (optionally DeepSeek-assisted; keep human gate). 2. Make scheduler
   cadence configurable from `config/settings.json`. 3. Phase 4 publisher ONLY on explicit owner request.

### Owner action needed
- None. Optional: review the real draft in the queue (`python -m review list`).
- Academy name / compliance jurisdiction still TBD. Phase 4 publishing needs explicit go-ahead.

### Tool / API decisions pending
- None blocking. Phase 4 will require choosing/authorizing real platform APIs (owner-gated).

### How to run
```bash
cd sportsverse-os
python main.py
python -m pytest
python scripts/check_live_llm.py
python -m review list
python -m scheduler list
```

---

## Session: 2026-06-09 (f) — DeepSeek selected + live activation prepared

**Agent:** Claude Code (Opus 4.8)
**Goal:** Owner chose **DeepSeek**. Install its SDK, pin the provider, prepare live mode.

### What was completed
- Owner selected provider: **DeepSeek** (OpenAI-compatible).
- Installed ONLY the required SDK: `openai` (v2.38.0) — no other SDKs installed.
- Pinned `.env`: `LLM_PROVIDER=deepseek` (already `LLM_MODE=live`).
- Updated `requirements.txt` (uncommented `openai`, noted DeepSeek).
- Added `scripts/check_live_llm.py` — one-command live verification for the owner.
- Verified routing: the router now targets `deepseek` and safely falls back to mock while the
  key is blank ("No live provider key found (tried 'deepseek'); using mock").

### Files created / edited
Created: `scripts/check_live_llm.py`. Edited: `.env` (LLM_PROVIDER=deepseek), `requirements.txt`,
`PROJECT_DNA.md`, `CURRENT_STATUS.md`, `OWNER_ACTION_REQUIRED.md`, this handoff.

### What was tested (results)
- `python -m pytest` → **44 passed**.
- `python scripts/check_live_llm.py` → mode=live, provider=deepseek, keys present=mock,
  `is_mock=True` (mock fallback) — correct, because the key is not pasted yet.

### Remaining (owner)
- **Paste the DeepSeek key** into the `DEEPSEEK_API_KEY=` line in `.env`, then run
  `python scripts/check_live_llm.py` (expect `is_mock: False`, "SUCCESS").
- Until then everything runs in safe mock fallback. Nothing publishes.

### Next recommended task
Once `check_live_llm.py` shows a real (non-mock) response, run a draft through the pipeline to
confirm real DeepSeek output, then proceed to Phase 3 (scheduler; no posting).

---

## Session: 2026-06-08 (e) — Phase 2C: Live LLM + Gated Automation

**Agent:** Claude Code (Opus 4.8)
**Phase:** 2C — live LLM setup (mock fallback) + 6-gate automation + audit logging
**Session goal:** Connect live LLM safely; add gated automation toward scheduling. No publishing.

### Provider note
Owner did not pick a provider in-session (dismissed the prompt). Per "do not install
unnecessary packages," NO SDK was installed. The live path supports all three providers and
**auto-detects** whichever single key is in `.env`. Owner just pastes a key + names the
provider; next agent installs that one SDK.

### What was completed
- **Live LLM router** (`core/llm_router.py`): `LLM_MODE=live` enables real calls; router picks
  provider by explicit arg > `LLM_PROVIDER` > task route > **first available real key**
  (auto-detect). Any missing key / SDK / error → **mock fallback with a logged reason** (never crashes).
- **Six-gate automation** (`review/automation.py`): gate1 draft_created, gate2 sentinel_review,
  gate3 compliance (risk < `COMPLIANCE_RISK_THRESHOLD`=50), gate4 owner_approval, gate5
  schedule_permission, gate6 preflight. All must pass for `approved_for_scheduled_publish`.
- **Full 8-status lifecycle** (`review/models.py`): draft_created, compliance_reviewed,
  ready_for_owner_review, owner_revision_requested, owner_rejected, owner_approved,
  approved_for_scheduled_publish, published_later_phase_only (reserved, never set).
- **Fourth owner action**: `approve_for_scheduled_publish` (gated). CLI `schedule` command added;
  `approve` now = approve-draft-only (`owner_approved`). `show` displays gate state.
- **Structured audit log** (`memory.log_audit` → `store/audit-<date>.jsonl`): ts, draft_id,
  action, agent, owner_decision, compliance_score, final_status. Hermes audits pipeline stages;
  ReviewService audits every owner action.
- **Compliance**: added `passed` (Gate 3) = risk below threshold; human approval still required.
- Created local `.env` with `LLM_MODE=live` + blank key lines (gitignored).

### Files created
`review/automation.py`; `tests/test_gates.py`; `tests/test_llm_live.py`; `.env`.

### Files edited
`core/llm_router.py`, `core/policy.py`, `agents/compliance.py`, `agents/hermes.py`,
`memory/manager.py`, `review/models.py`, `review/store.py` (via models), `review/service.py`,
`review/cli.py`, `review/__init__.py`, `scripts/smoke_review.py`, `tests/test_review.py`,
`main.py` (banner), and docs (PROJECT_DNA, CURRENT_STATUS, NEXT_STEPS, OWNER_ACTION_REQUIRED, README).

### What was tested (results)
- `python -m pytest` → **44 passed** (exit 0). New tests prove: live provider used when key
  exists (network mocked); auto-detect of whichever key is present; missing key → mock fallback;
  provider error → mock fallback; owner approval required before scheduling; scheduled status only
  via owner action; compliance failure blocks scheduling; schedule-block is audited; reject stays
  archived; all actions logged to events + audit; nothing publishes.
- `python scripts/smoke_review.py` → 4 drafts → compliance → queue → all 4 owner actions →
  6 gates pass for scheduling → high-risk item BLOCKED at gate3 → `any_published=False`. Prints full audit log.
- **Live draft test** (`build_system`, `.env` `LLM_MODE=live`, no key): logged
  "No live provider key found ... using mock", produced a draft via mock fallback. is_mock=True.

### What failed
- Nothing functional. Fixed two cosmetic Windows-console em-dashes (→ ASCII).

### Known bugs
- None. Real provider calls only run with a key in `.env` + that SDK installed.

### Current architecture
Adds `review/automation.py` (gates) and the audit log. LLM router now live-capable with
auto-detect + mock fallback. Pipeline unchanged through compliance; ends in the gated review
queue. Approval and scheduling both leave `published=False`. No publish/scheduler EXECUTION exists.

### Current phase
Phase 2C — **complete.** Next: finish live activation (owner key + one SDK), then Phase 3 scheduler (no posting).

### Next recommended task
1. When owner pastes a key + names provider: `pip install anthropic` OR `pip install openai`
   (DeepSeek uses openai), run a draft, confirm `is_mock=False`. 2. Deepen Compliance checks.
   3. Phase 3 = scheduler that proposes times for `approved_for_scheduled_publish` items (still no posting).

### Owner action needed
- Paste ONE provider key into `.env` (already `LLM_MODE=live`) and tell the agent which provider.
- Optional: review drafts via `python -m review ...`. Academy name / jurisdiction still TBD.

### Tool / API decisions pending
- Which provider (Anthropic / OpenAI / DeepSeek) — owner; determines the single SDK to install.

### How to run
```bash
cd sportsverse-os
python main.py
python -m pytest
python scripts/smoke_review.py
python -m review list
```

---

## Session: 2026-06-08 (d) — Phase 2B: Owner-Review Surface

**Agent:** Claude Code (Opus 4.8)
**Phase:** 2B — owner-review surface (approve / reject / request-revision)
**Session goal:** Build the human approval gate in mock mode. No publishing, no auto-posting.

### What was completed
- **Owner-review queue** (`review/`): file-based, portable persistence of drafts as review
  items (`reports/review/<id>.json`; rejected → `archive/`). Statuses:
  `ready_for_owner_review`, `approved_for_future_publish`, `rejected`, `revision_requested`.
- **ReviewService** with three owner actions: `approve` (→ approved_for_future_publish,
  **never publishes**, `published` stays False), `reject` (archives with a **required**
  reason), `request_revision` (creates a Hermes/OpenClaw revision Task → new draft re-enters
  the queue). Every action logged to memory.
- **CLI**: `python -m review list | show | approve | reject --reason | revise --notes`.
- **Hermes** now auto-submits finished drafts to the queue and returns `review_id`.
- Smoke script `scripts/smoke_review.py` (isolated temp dirs) demonstrates the full flow.

### What was changed
- `agents/hermes.py` (review_store param + `_submit_for_review` + `review_id` in result).
- `main.py` (wire `ReviewStore`; banner shows pending count; "Phase 2B boot").
- `core/paths.py` (`REVIEW_DIR` + ensure_runtime_dirs).
- `.gitignore` (ignore `reports/review/*` except `.gitkeep`).

### Files created
`review/{__init__,models,store,service,cli,__main__}.py`; `reports/review/.gitkeep`;
`scripts/smoke_review.py`; `tests/test_review.py`.

### Files edited
`agents/hermes.py`, `main.py`, `core/paths.py`, `.gitignore`,
`PROJECT_DNA.md`, `CURRENT_STATUS.md`, `NEXT_STEPS.md`, `OWNER_ACTION_REQUIRED.md`, `README.md`.

### What was tested (results)
- `python -m pytest` → **35 passed** (exit 0). New `test_review.py` proves: draft appears in
  the surface; approve sets `approved_for_future_publish` with `published=False`; review item
  and service have NO publish method; reject archives with reason (and requires one); revision
  creates a Hermes task + a new queued draft; all review actions logged to memory.
- `python scripts/smoke_review.py` → 3 drafts created (mock) → compliance reviewed → queued →
  approve / reject / revise → `any_published=False`. Output shows the memory audit trail.
- `python -m review list` / `approve <id>` → CLI cycle verified (list → approve → empty).

### What failed
- Two minor fixes during the session: smoke script needed a `sys.path` bootstrap (it lives in
  `scripts/`); one CLI em-dash switched to ASCII for the Windows console. Both fixed.

### Known bugs
- None. Mock mode throughout; nothing publishes.

### Current architecture
Adds `review/` (queue + service + CLI) to the stack. Pipeline now ends in the owner-review
queue: NL → classify → Sentinel → OpenClaw (draft-only) → Compliance → **owner review**.
Approval only sets `approved_for_future_publish`; there is no publishing code anywhere.

### Current phase
Phase 2B — **complete.** Next is Phase 2C (real LLM responses once owner supplies a key).

### Next recommended task
1. Owner adds ONE provider key + `LLM_MODE=live`; verify real drafts. 2. Deepen Compliance
   checks. 3. (Optional) HTML view of the review queue. Keep approval ≠ publishing.

### Owner action needed
- None required. Optional: review drafts via `python -m review ...`; add an LLM key for real drafts.
- Academy brand name (TBD); compliance jurisdiction (TBD).

### Tool / API decisions pending
- LLM provider choice (Anthropic / OpenAI / DeepSeek) — owner. Default stays mock.

### How to run
```bash
cd sportsverse-os
python main.py                     # boot
python -m pytest                   # tests
python scripts/smoke_review.py     # owner-review demo
python -m review list              # review drafts
```

---

## Session: 2026-06-08 (c) — Phase 2A: Real LLM Router + Delegation + Draft Skills

**Agent:** Claude Code (Opus 4.8)
**Phase:** 2A — LLM router + Hermes→OpenClaw delegation + draft-only skills
**Session goal:** Build the next *safe* layer. No auto-publishing, no live posting, no paid tools.

### What was completed
- **LLM router with provider abstraction**: `core/providers/` (base, mock, openai, anthropic,
  deepseek). **Mock is the default** (no network). Keys only from `.env`. Live mode falls back
  to mock if a key/SDK is missing — a missing key never crashes the system.
- **Hermes→OpenClaw delegation pipeline**: Hermes receives NL → `classify()` → Sentinel
  `review_skill()` → OpenClaw runs a whitelisted **draft-only** skill → Compliance
  `review_draft()` (risk score + notes) → result `ready_for_owner_review` (`published=False`).
- **Whitelist skill registry** (`skills/registry.py`) + six draft-only skills
  (`skills/drafts.py`): sports_topic_research_draft, video_idea_draft, script_outline_draft,
  affiliate_product_research_draft (medium risk), compliance_review_draft, daily_report_draft.
  Each declares name/purpose/risk/allowed/prohibited/approval. Registry refuses non-draft or
  forbidden-action skills.
- **Sentinel**: `review_skill()` blocks high-risk by default and logs blocks/warnings to memory.
- **Compliance**: `review_draft()` adds a 0-100 heuristic risk score + notes; never auto-approves.
- **Memory audit log**: `log_event()` / `read_events()` record tasks, outputs, warnings, decisions.
- **`core/policy.py`**: single source of truth for FORBIDDEN_ACTIONS + blocked risk levels.

### What was changed
- Rewrote `core/llm_router.py`, `agents/hermes.py`, `agents/openclaw.py`, `agents/sentinel.py`,
  `agents/compliance.py`. Edited `agents/base.py` (new `ready_for_owner_review` status),
  `memory/manager.py` (audit log), `main.py` (wire registry; banner shows LLM mode + skills),
  `.env.example` (`LLM_MODE`, `DEEPSEEK_API_KEY`), `config/settings.example.json`.
- Updated docs: PROJECT_DNA, CURRENT_STATUS, NEXT_STEPS, OWNER_ACTION_REQUIRED, api_keys_needed.

### Files created
`core/policy.py`; `core/providers/{__init__,base,mock,openai_provider,anthropic_provider,deepseek_provider}.py`;
`skills/{__init__,base,registry,drafts}.py`;
`tests/{test_llm_router,test_skills,test_delegation}.py`.

### Files edited
`core/llm_router.py`, `agents/{base,hermes,openclaw,sentinel,compliance}.py`, `memory/manager.py`,
`main.py`, `.env.example`, `config/settings.example.json`, `tests/test_agents.py`,
`PROJECT_DNA.md`, `CURRENT_STATUS.md`, `NEXT_STEPS.md`, `OWNER_ACTION_REQUIRED.md`, `docs/api_keys_needed.md`.

### What was tested  (results)
- `python -m pytest` → **28 passed** (exit 0). Covers: mock mode works without keys; missing
  keys don't crash live mode; all providers registered; six skills present + draft-only +
  cannot publish; registry rejects forbidden-action skill; Hermes delegates to OpenClaw and
  marks ready-for-review; OpenClaw blocks unregistered + high-risk skills; Sentinel blocks
  high-risk and logs to memory; Compliance required before owner review; memory logs the task.
- `python main.py` → boots cleanly. End-to-end smoke (mock): NL "draft some video ideas" →
  `ready_for_owner_review`, skill `video_idea_draft`, risk 0, `published=False`, draft produced.

### What failed
- Nothing. (Fixed two cosmetic Windows-console em-dash glitches by using ASCII.)

### Known bugs
- None. Real provider call code exists but only runs in `LLM_MODE=live` with a key + SDK.

### Current architecture
Python under `sportsverse-os/`: `core/` (+`providers/`), `agents/` (5 agents), `skills/`
(registry + 6 draft skills), `memory/` (manager + audit log), `integrations/` (dry-run),
`workflows/` (approval gate), `config/`, `tests/` (28). Mock-first, draft-only, human-gated.

### Current phase
Phase 2A — **complete**. Ready for Phase 2B (real LLM responses once owner supplies a key).

### Next recommended task
1. Owner adds ONE provider key to `.env` + sets `LLM_MODE=live`; install that SDK; verify a
   real (non-mock) draft returns. 2. Deepen Compliance checks. 3. Add an owner-review surface
   (list `ready_for_owner_review` drafts to approve/reject). Keep everything draft-only.

### Owner action needed
- (When ready) choose LLM provider (Anthropic / OpenAI / DeepSeek), add key, set `LLM_MODE=live`.
- Academy brand name (TBD); compliance jurisdiction (TBD).

### Tool / API decisions pending
- **LLM provider choice** (Anthropic / OpenAI / DeepSeek) — owner. Default stays mock until chosen.

### How to run
```bash
cd sportsverse-os
python main.py          # boot the org
python -m pytest        # run tests (pip install pytest if missing)
```

---

## Session: 2026-06-08 (b) — Phase 1 Python Skeleton

**Agent:** Claude Code (Opus 4.8)
**Phase:** 1 — Core Agent Framework
**Session goal:** Build the Python agent-framework skeleton (not full production agents).

### What was completed
- Confirmed tech stack = **Python** (owner decision).
- Filled in all previously-`[TBD]` business facts from the owner's Sportsverse plan
  (brand structure, agents, focus, safety rules) across `PROJECT_DNA.md`.
- Built the full Phase 1 **skeleton** and verified it runs and tests pass.

### What was changed
- Updated `PROJECT_DNA.md` (sections 1–11, 14, 15: business facts, Python stack, progress).
- Updated `CURRENT_STATUS.md`, `NEXT_STEPS.md`, `OWNER_ACTION_REQUIRED.md`.
- Updated `.gitignore` (added `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/`).
- Made `main.py` banner ASCII-only (Windows/VPS console safe).

### Files created (Phase 1)
**Project:** `main.py`, `pyproject.toml`, `requirements.txt`, `conftest.py`
**core/:** `__init__.py`, `paths.py`, `config.py`, `logging_setup.py`, `llm_router.py`
**agents/:** `__init__.py`, `base.py`, `hermes.py`, `openclaw.py`, `sentinel.py`, `archivist.py`, `compliance.py`
**memory/:** `__init__.py`, `manager.py`
**integrations/:** `__init__.py`, `telegram_interface.py`, `email_report.py`
**workflows/:** `__init__.py`, `runner.py`
**config/:** `settings.example.json`
**tests/:** `__init__.py`, `test_imports.py`, `test_config.py`, `test_agents.py`, `test_compliance.py`, `test_memory.py`

### Files edited
`PROJECT_DNA.md`, `CURRENT_STATUS.md`, `NEXT_STEPS.md`, `OWNER_ACTION_REQUIRED.md`, `.gitignore`, `main.py`.

### What was tested
- `python main.py` → boots the org (Hermes + OpenClaw/Sentinel/Archivist/Compliance registered). Clean, no errors.
- `python -m pytest` → **15 passed in 0.34s** (exit 0).
- Tests cover: imports/assembly, config + `.env` parser, agent registration/delegation,
  publishing-disabled-by-default, OpenClaw skill execution, Compliance never auto-approves,
  workflow approval gate blocks, and memory create/read/list/recall/forget.

### What failed
- Nothing. (One cosmetic console-encoding issue with box-drawing chars in the banner was
  fixed by switching the banner to ASCII.)

### Known bugs
- None. All non-infrastructure modules are intentional stubs (no real LLM/network/posting).

### Current architecture
Python framework under `sportsverse-os/`:
`core/` (paths, config, logging, llm_router) · `agents/` (base + 5 agents) ·
`memory/` (file-based manager) · `integrations/` (telegram + email, dry-run) ·
`workflows/` (runner with human-approval gate) · `config/` · `tests/` · `main.py`.
Functional now: config, logging, memory, workflow gate, agent wiring.
Stubbed (no network): LLM router, Telegram/email sending, Hermes planning, Compliance checks.

### Current phase
Phase 1 — Core Agent Framework. **Skeleton complete.** Ready for Phase 2 (real behaviour).

### Next recommended task
Phase 2, per `NEXT_STEPS.md`:
1. Implement key-guarded `LLMRouter.complete()` for one provider.
2. Real Hermes→OpenClaw delegation.
3. First *draft-only* OpenClaw skills (no posting).
Keep integrations dry-run; never publish without human approval.

### Owner action needed
- Choose first LLM provider + supply API key (only to enable real AI responses).
- Provide Academy brand name (TBD).
- Confirm compliance jurisdiction (TBD).
(Stack + business facts are now resolved.)

### Tool / API decisions pending
- **LLM provider:** Anthropic vs OpenAI — UNDECIDED. Router defaults to Anthropic model
  IDs as placeholders; no key required until Phase 2 implements real calls.
- Sports data provider, messaging/email go-live: later phases.

### How to run
```bash
cd sportsverse-os
python main.py          # boot the org
python -m pytest        # run tests (pip install pytest if missing)
```

---

## Session: 2026-06-08 (a) — Phase 0 Foundation Build

**Agent:** Claude Code (Opus 4.8) · **Phase:** 0 — Portable Foundation

- Created the portable root `sportsverse-os/` with the full subfolder structure.
- Created the five continuity files, constitution + approval rules, architecture +
  memory-schema docs, `.env.example` + `.gitignore`, `docs/api_keys_needed.md`,
  `deployment/vps_setup_guide.md`, `security/security_policy.md`, and this handoff system.
- No code yet (foundation only). Nothing failed.

---

<!-- Add the next session's handoff ABOVE the most recent one (newest first), or copy
     this file to handoff_YYYY-MM-DD.md and start fresh. -->
