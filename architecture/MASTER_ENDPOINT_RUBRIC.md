# MASTER ENDPOINT RUBRIC — Sportsverse OS

> The **final endpoint vision** for Sportsverse OS and an honest status of each item against the
> current build (verified 2026-06-28, `python -m pytest` → **134 passing**, deployed on the VPS).
> Status legend: **Built** · **Partial** (works but incomplete) · **Not built** · **Refactor** (exists,
> needs rework) · **Blocked: owner** (needs an owner credential/decision) · **Blocked: external**
> (needs a third-party API/tool/audit).

Foundational principle (LOCKED): **DeepSeek stays the default low-cost LLM**; everything sits behind
provider abstractions so OpenAI / Claude / NVIDIA-Nemotron can be added later. No paid-tool lock-in.
Open-source / local first.

| # | Endpoint item | Status | Evidence / what's missing |
|---|---------------|--------|---------------------------|
| 1 | **Hermes (CEO/router)** | **Built** | `agents/hermes.py` — classifies, routes, flags gated actions; final decision-maker. |
| 2 | **Sentinel** | **Partial** | `agents/sentinel.py` — skill-permission review + block high-risk + memory log working; broader drift/integrity scans are stubs. |
| 3 | **Archivist** | **Partial / Refactor** | `agents/archivist.py` skeleton; memory writes work via `MemoryManager`; automated handoff-writing is a stub. |
| 4 | **Compliance Office** | **Built** | `agents/compliance.py` — per-dimension `pass/warn/flag` heuristics, risk 0–100, Gate 3; never auto-approves. Optional DeepSeek assist off by default. |
| 5 | **OpenClaw under Hermes** | **Built** | `agents/openclaw_skill_agent.py` + `config/openclaw_allowlist.json` — allowlist-only, draft-only, no secrets/shell/publish; every call logged. |
| 6 | **Sports Data Hub** | **Built** | `sports/` — ESPN (keyless) + API-Football clients, SQLite cache + stale fallback, health monitor + Telegram alerts, `SportsContext` agent integration. Live on VPS. |
| 7 | **Research Department** | **Partial** | `agents/research_agent.py` (DeepSeek drafts) + sports grounding. No `last30days` trend skill; no web/Reddit/X/YouTube research providers. |
| 8 | **Content Department** | **Built** | `agents/content_agent.py` — DeepSeek drafts, sports-grounded, flow into review queue. Hooks/titles/descriptions work; CTA/template packs informal. |
| 9 | **Video Department** | **Not built** (metadata only) | `agents/video_agent.py` produces concept/script/metadata drafts; **never renders/edits/uploads**. No assembly, trim, caption-burn, render, or export. |
| 10 | **Creative Department** | **Not built** | No thumbnail/layout/title-card/brand-styling agent. See `CREATIVE_STUDIO_PLAN.md`. |
| 11 | **Social Department** | **Partial** | `publishing/` adapters (YouTube/IG/TikTok) + `PublishingService` behind approval; `agents/social_publishing_agent.py`. Code only — **Blocked: owner** (no creds) + not deployed. |
| 12 | **Marketing Department** | **Not built** | No growth/campaign/SEO agent. |
| 13 | **Website Department** | **Partial** | Static site live (`website/`, nginx); `agents/dns_website_agent.py` is guidance/verify only — no content automation. |
| 14 | **Community Department** | **Not built** | No comment/DM (template-only) handling agent. |
| 15 | **Commerce Department** | **Not built** | Affiliate-intelligence is concept only; no commerce agent/skills. |
| 16 | **Analytics Department** | **Partial** | `agents/analytics_agent.py` file-based metrics + owner-preference learning; no live platform stats (arrives with publishing). Dashboard Analytics = placeholder. |
| 17 | **Development Department** | **Partial** | `agents/coding_agent.py` — DeepSeek code drafts only (no apply/exec). |
| 18 | **Technology Scout** | **Not built** | No agent that scouts/evaluates new tools/skills/providers. |
| 19 | **Dashboard-native video editor** | **Not built** | This audit's main new plan. See `CREATIVE_STUDIO_PLAN.md`. |
| 20 | **Dashboard-native thumbnail editor/generator** | **Not built** | Planned in `CREATIVE_STUDIO_PLAN.md` (Pillow/SVG-first). |
| 21 | **Owner review queue** | **Built** | `review/` (8-status lifecycle) + dashboard **Approvals**; approve/reject/request-edit/schedule, all audited. |
| 22 | **Gated automation** | **Built** | `approval/` gates + `scheduler/` (proposes times, never posts) + cost gate in `model_router`. |
| 23 | **YouTube publishing behind gates** | **Partial / Blocked: owner** | `publishing/youtube.py` + service + dashboard publish action; defaults to `private`. Needs OAuth creds; not deployed. |
| 24 | **Future IG/TikTok behind gates** | **Partial / Blocked: external** | `publishing/{instagram,tiktok}.py` exist; IG needs Meta App Review, TikTok needs app audit (draft-only until then); both need owner creds. |
| 25 | **Knowledge Library** | **Not built** | `knowledge_library/` is a README only. No article/source/idea/competitor store or Hermes search. |
| 26 | **Shared persistent memory** | **Partial** | `memory/manager.py` (file memory + event + audit log) + `orchestration/journal.py`. Works but minimal; not a searchable knowledge graph. |
| 27 | **Department skill packs** | **Not built / Refactor** | `skills/` has 6 flat draft skills + whitelist registry. Not organized into reusable department packs. |
| 28 | **Plugin/provider abstraction** | **Partial** | LLMProvider (`providers/`, `core/providers/`) + PublishingProvider (`publishing/base.py`) exist. Missing: VideoEditorProvider, ThumbnailProvider, CaptionProvider, ResearchProvider. See `PLUGIN_PROVIDER_MAP.md`. |
| 29 | **VPS deployment readiness** | **Built** | Live on Hostinger VPS — nginx + Let's Encrypt SSL + systemd (`sportverse`, `sportverse-dashboard`); GitHub backup. |
| 30 | **Portable project DNA / handoff** | **Built / Refactor** | Continuity files + `reports/handoff/*`. System exists; several files drifted stale (fixed in this audit). |

## Rollup
- **Built (12):** 1, 4, 5, 6, 8, 21, 22, 29, 30 + provider/LLM core, review, gates.
- **Partial (11):** 2, 3, 7, 11, 13, 16, 17, 23, 24, 26, 28.
- **Not built (7):** 9, 10, 12, 14, 15, 18, 19, 20, 25, 27 *(creative/video/thumbnail, marketing, community, commerce, tech-scout, knowledge library, skill packs)*.
- **Headline:** the **operating core, sports data, review/gates, and deploy are solid**; the **creative/video production surface is the biggest missing capability**, and several "departments" are placeholder agents, not real pipelines.

## Estimated completion vs this endpoint vision: **~55–60%**
(Operating core ≈ 90%, sports ≈ 95%, publishing ≈ 60% code / 0% live, creative/video ≈ 5%,
departments breadth ≈ 35%, knowledge/memory ≈ 40%.)

## Recommended next phase
**Phase 6 — Dashboard-native Creative Studio (V1, plan-first).** Highest owner value, fills the
largest gap, and is achievable open-source/local (FFmpeg + MoviePy + Pillow) with no paid lock-in.
Detailed in `CREATIVE_STUDIO_PLAN.md`; gap math in `BUILD_GAP_ANALYSIS.md`.
