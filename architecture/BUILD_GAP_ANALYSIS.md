# BUILD GAP ANALYSIS — Sportsverse OS (2026-06-28)

> Honest audit of the current build vs the full endpoint vision (`MASTER_ENDPOINT_RUBRIC.md`).
> Verified against the repo; `python -m pytest` → **134 passing**; deployed on the Hostinger VPS.
> **No major features were built during this audit** (per instruction). This is analysis + recommendation.

## 1. What is already built (solid)
- **Operating core:** Hermes (router/decider), Jarvis (interface), LangGraph orchestration + built-in
  fallback, cost-aware model router (**DeepSeek default**, Nemotron optional), OpenClaw whitelist skill
  adapter, agent journal.
- **Governance:** owner review queue (8-status lifecycle), approval gates, scheduler (proposes times,
  never posts), Compliance Office (per-dimension heuristics, Gate 3), audit logging.
- **Sports Data Hub:** ESPN + API-Football, SQLite cache + stale fallback, health monitor + Telegram
  alerts, `SportsContext` (direct answers with no LLM spend + grounding briefs into agents). Live.
- **Dashboard:** 16 sections, login + Telegram 2FA, server-rendered, session-gated actions. Live.
- **Comms:** Telegram bot (control/alerts/2FA), real Gmail email reports.
- **Infra:** VPS deploy (nginx + Let's Encrypt SSL + systemd), GitHub backup (.env excluded).
- **Publishing (code):** YouTube/IG/TikTok adapters + `PublishingService` behind approval; dashboard
  publish action; draft/private defaults; "not configured" when creds absent.

## 2. What is partially built
- **Sentinel / Archivist** — skill-permission review + memory work; broader integrity/drift scans and
  automated handoff-writing are stubs.
- **Departments as placeholders** — Research, Analytics, Development, Website are single skeleton agents,
  not full pipelines. Content is the most complete (real DeepSeek drafts, sports-grounded, review-wired).
- **Publishing live** — code is ready but **not deployed** and **blocked on owner credentials**.
- **Provider abstraction** — LLM + Publishing exist; Video/Thumbnail/Caption/Research providers do not.
- **Memory** — functional file-based memory + journal; not a searchable Knowledge Library.

## 3. What is missing
- **Dashboard-native Creative Studio** (video editor + thumbnail editor) — the largest gap.
- **Video Department** real pipeline (assemble/trim/caption-burn/render/export). Today: metadata drafts only.
- **Creative, Marketing, Community, Commerce, Technology Scout** departments — not built.
- **Knowledge Library** — store + Hermes search.
- **Department skill packs** — skills exist but aren't organized/reusable as packs.
- **Live platform analytics** — arrives with publishing.

## 4. What must be built next (recommended order)
1. **Creative Studio V1a** — `VideoProject` model + `FfmpegVideoEditor` + `PillowThumbnailProvider`
   (local, offline-tested, CLI render; no UI). *(Plan: `CREATIVE_STUDIO_PLAN.md`.)*
2. **Creative Studio V1b** — replace the placeholder Video Review with the **Creative Studio UI**
   (preview, clip list/trim/reorder, caption edit, thumbnail) wired through providers; background render
   + Telegram "draft ready" ping.
3. **Creative Studio V1c** — "Request AI revision" (DeepSeek) + compliance re-check on each render +
   approve → review/scheduler wiring.
4. **Reorganize skills into department packs** (`DEPARTMENT_SKILL_MAP.md`) — low risk, enables growth.
5. **Deploy + credential the publisher** (owner action) so approved videos can reach YouTube (private).

## 5. Does the current architecture support dashboard-native video editing?
**Yes — additively, no rewrite.** The dashboard's server-rendered + session-gated action pattern, the
review/approval/scheduler gates, the audit/journal, the OpenClaw whitelist, and the proven provider
pattern (`providers/`, `publishing/`) all extend to a Creative Studio. New pieces are local/open-source:
**video/thumbnail/caption provider impls, a VideoProject store, and the Studio UI.** Hard requirement:
**FFmpeg installed on the VPS** (free; one `apt install`).

## 6. Refactors needed (small, safe)
- **Skills → department packs** (`skills/packs/…`) without breaking the registry/whitelist.
- **Archivist** — make handoff-writing real (auto-update `latest_handoff.md` + DNA stamps).
- **Continuity files** — keep PROJECT_DNA/CURRENT_STATUS/NEXT_STEPS/README in sync (drifted; corrected
  in this audit). Brand naming: standardize on **Sportsverse** + domain **sportsversenews.com**
  (legacy "SportsVersusNews"/"sportsverselabs" strings remain in older docs/agent prompts — cosmetic).
- **Add provider interfaces** for video/thumbnail/caption/research mirroring `publishing/base.py`.

## 7. Recommended next phase
**Phase 6 — Dashboard-native Creative Studio (V1a → V1c).** Build **plan-first**, then implement V1a
(local render foundation + offline tests) since the existing structure safely allows it. This delivers
the owner's top-requested capability (preview/edit/approve videos in-dashboard), stays open-source/local,
adds no paid lock-in, and preserves every safety rule.

### Safety carried into Phase 6 (LOCKED)
No auto-publishing · no public posting without approval · edited content re-runs compliance · no
unapproved OpenClaw skills · no secrets in logs · no paid-tool lock-in · all owner decisions logged.

## 8. Blockers
- **Owner:** publisher credentials (YouTube OAuth, IG token, TikTok keys); decision to provision FFmpeg
  on the VPS (free).
- **External:** IG Meta App Review; TikTok app audit (draft-only until then).
