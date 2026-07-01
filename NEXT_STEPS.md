# NEXT_STEPS.md

> Direct instructions for the **next coding agent**.
> Read `PROJECT_DNA.md` and `CURRENT_STATUS.md` first, then do these in order.
> Last updated: 2026-07-01

---

## Where we are now (2026-07-01)
YouTube private publishing is configured and verified for PlatinumClips, but still owner-gated.
Instagram and TikTok remain pending setup. Creative Studio can render/thumbnail projects when media exists,
and the VPS smoke passes. The current live browser QA found the next real gap: Ask Hermes creates a review
text draft, not a renderable Creative Studio video project. The rendered demo video is technically valid
but generic, not soccer highlight-style.

## Do These Next (current order)

1. **Wire Hermes video prompts into Creative Studio projects.** For video-draft prompts, create a
   `VideoProject`, carry title/description/captions/thumbnail idea into the Studio record, and link the
   Review item back to the project id.
2. **Add a safe soccer visual source path.** Use generated/licensed/owner-uploaded clips or a template-only
   commentary format. Do not use broadcast footage unless the owner supplies rights/permission.
3. **Render a prompt-matched 30-second draft in-dashboard.** Verify thumbnail preview, video preview,
   captions, pacing, compliance report, pipeline counts, Publishing status, and no publish.
4. **Keep publish history honest.** YouTube Studio shows two private verification uploads and the VPS
   Publishing History panel now shows both after backfill. Future uploads should be logged by the VPS path.
5. **Keep Instagram/TikTok setup parked** until owner app approval/OAuth setup resumes.

## Where we are (2026-06-28)
Phases 0–4 complete; Phase 5 (publishing) **code complete behind gates**; **deployed live** on the VPS.
Stack is **Python + `openai` SDK** (DeepSeek live). `python -m pytest` → **184 tests** pass.
- Hermes Operating Core: Jarvis → Hermes → cost router → worker → compliance → approval → execution → journal.
- **Sports Data Hub live** (ESPN + API-Football, cache, health, Telegram alerts, agent grounding).
- **Dashboard live** (16 sections, login + Telegram 2FA); **email reports live**; **publisher code** ready
  (YouTube/IG/TikTok adapters behind approval — needs owner creds; not yet deployed/credentialed).
- **DeepSeek default; Nemotron optional** (off → fallback). LangGraph optional. Hermes is final router;
  nothing publishes/spends/installs without a gated approval; `execution_agent` takes no external action.

## ▶ RECOMMENDED NEXT PHASE — Phase 6: Dashboard-native Creative Studio
Per the 2026-06-28 endpoint audit (`architecture/BUILD_GAP_ANALYSIS.md`), the biggest gap is a
**dashboard-native video + thumbnail editor** so the owner can preview/edit/approve draft videos in the
dashboard (no CapCut/Canva/Synthesia for the basic flow). **Plan-first, then build V1a.**
- Read first: `architecture/CREATIVE_STUDIO_PLAN.md`, `MASTER_ENDPOINT_RUBRIC.md`, `PLUGIN_PROVIDER_MAP.md`.
- **V1a:** `VideoProject` model + `FfmpegVideoEditor` + `PillowThumbnailProvider` (local, offline tests, CLI render — no UI). Requires **FFmpeg on the VPS** (free apt install).
- **V1b:** Creative Studio dashboard section (preview, clip list/trim/reorder, caption edit, thumbnail) via providers + background render + Telegram "draft ready" ping.
- **V1c:** "Request AI revision" (DeepSeek) + compliance re-check per render + approve → review/scheduler.
- Open-source/local first; everything behind provider interfaces; all safety rules LOCKED (no auto-publish,
  edited content re-runs compliance, no unapproved skills, no secrets in logs, no paid lock-in, decisions logged).

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
