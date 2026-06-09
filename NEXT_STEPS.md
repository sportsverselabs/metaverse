# NEXT_STEPS.md

> Direct instructions for the **next coding agent**.
> Read `PROJECT_DNA.md` and `CURRENT_STATUS.md` first, then do these in order.
> Last updated: 2026-06-09

---

## Where we are
Phases 0–4 are complete. Stack is **Python + `openai` SDK** (DeepSeek live).
- `python -m pytest` → **79 tests** pass.
- **Phase 4 Hermes Operating Core** runs: Jarvis → Hermes router → cost router → worker agent
  (research/content/coding/nemotron/openclaw) → compliance → approval gate → execution → journal.
- **DeepSeek default; Nemotron optional** (disabled → fallback to DeepSeek). LangGraph optional
  (auto-detected; built-in runner otherwise). Both verified.
- **Hermes is the final router/decision-maker.** No sub-agent publishes/spends/sends/installs/
  changes production without a gated approval. `execution_agent` performs NO external action.

## How to run
```bash
cd sportsverse-os
python -m pytest                                    # 79 tests
python scripts/smoke_phase4.py                      # operating-core demo (mock, isolated)
python -m orchestration "research trending stories" # live Jarvis -> Hermes core (DeepSeek)
python -m approval list                             # gated-action approvals
python -m review list ; python -m scheduler list    # Phase 2/3 surfaces (still work)
```

## How the model router decides (Phase 4)
- DeepSeek for routine: summaries, drafts, normal research, basic code edits, logs, reports.
- Nemotron ONLY for: reasoning, planning, architecture, long-context, multimodal, high-value
  decisions — and only if `NEMOTRON_ENABLED=true` + key + base URL; else DeepSeek.
- Over per-task threshold or monthly budget (`config/model_budget.json`) → human approval BEFORE spend.

---

## Recently completed (2026-06-09 follow-ups)
- ✅ **Deepened Compliance** (`agents/compliance.py`): real per-dimension heuristics
  (`pass`/`warn`/`flag` + notes); any `flag` fails Gate 3; still never auto-approves.
- ✅ **Wired orchestration → review queue**: `content_agent` drafts that pass compliance are
  queued into `review/` (`execution_agent`), so a command flows command → DeepSeek → compliance →
  `python -m review` → `python -m scheduler`. Verified live.
- ✅ **UTF-8-safe CLIs** (`core/console.py`) so emoji/em-dash model output prints on Windows.

## Do These Next (in order)

1. **(Optional infra) Enable the real engines.** `pip install langgraph` to use LangGraph; set
   `NEMOTRON_ENABLED=true` + `NEMOTRON_API_KEY` + `NEMOTRON_BASE_URL` (+ `NEMOTRON_MODEL`) to use
   Nemotron. Both auto-detected — no code change. Verify with `python -m orchestration "..."`.

2. **Per-platform compliance refinement**: tailor checks/notes per target platform
   (YouTube/TikTok/Instagram), optionally DeepSeek-assisted via `Compliance.llm_assist` (kept off
   by default for cost/determinism). Keep the human gate; never auto-approve.

3. **Broaden review-queue feeding** if desired: currently only `content_agent` auto-queues
   (`SUBMIT_TO_REVIEW_ROUTES` in `orchestration/routes.py`). Consider script_outline/skill drafts.

4. **Phase 5 — Publisher (DO NOT START without explicit owner instruction).** The ONLY place real
   platform APIs (YouTube/TikTok/Instagram/Telegram/email/website/Hostinger) are added, behind
   explicit per-item owner approval. This is where a gated, approved action is finally executed.

5. **Update continuity files** at session end.

---

## Do NOT Work On These Yet (locked)

- ⛔ **Executing any gated action** (publish/post/email/spend/install/VPS/payment). Phase 5 only,
  with explicit owner sign-off. `execution_agent` must stay a no-op for external actions.
- ⛔ Adding OpenClaw skills to the allowlist without owner approval (it's a gated action).
- ⛔ Removing the mock fallback, the cost gate, or any approval gate.
- ⛔ Printing secrets to logs. Installing more LLM SDKs than needed.

---

## Ask The Owner Only If Required
Per `constitution/approval_rules.md`. Pending owner inputs (non-blocking): whether to enable
LangGraph/Nemotron, Academy brand name, compliance jurisdiction. **Phase 5 (real publishing/
production actions) requires explicit owner go-ahead.**
