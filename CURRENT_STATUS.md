# CURRENT_STATUS.md

> Live snapshot of where the project is **right now**.
> Update this at the start and end of every coding session.

| Field | Value |
|---|---|
| Last updated | 2026-07-01 |
| Updated by | Coding Agent (Codex) |

---

## 🟢 LIVE / DEPLOYED (2026-06-10)
The system is **deployed and operating in production** on the Hostinger VPS.

- **Backed up to GitHub:** github.com/sportsverselabs/metaverse (public; secrets excluded via .gitignore).
- **VPS:** Hostinger Ubuntu 24.04 at the IP in `.env` `VPS_HOST`. Code at `/root/metaverse`, deps in `.venv`.
  Agent's SSH key is in root's `authorized_keys` (key `id_ed25519`). 100 tests pass on the server.
- **DeepSeek:** live & verified on the VPS (`LLM_MODE=live`).
- **Telegram bot:** `@Sportsversebot` — systemd service `sportverse` (run_telegram.py), running 24/7,
  locked to the owner's chat id. Token in VPS `.env`.
- **Website/dashboard:** nginx reverse-proxy → `sportverse-dashboard` service (read-only dashboard on
  127.0.0.1:8787), HTTP-basic-auth protected, HTTPS via Let's Encrypt (auto-renew). Live at
  **https://sportsversenews.com**, `www`, and `dashboard.` subdomain. Config files in `deployment/`.
- **Domain:** sportsversenews.com (A records @/www/dashboard → VPS). SSL OK; HTTP→HTTPS redirect.
- **Secrets** (DeepSeek key, Telegram token, dashboard password) live ONLY in VPS `.env` / `/etc/nginx/.htpasswd`
  — never committed. To redeploy/update: `cd /root/metaverse && git pull && systemctl restart sportverse sportverse-dashboard`.

---

## Current Development Phase
**Current snapshot (2026-07-01): Phase 5 YouTube is live behind gates; Phase 6 Creative Studio is deployed but needs prompt-to-render wiring.**
YouTube OAuth is configured for **PlatinumClips** private uploads. Instagram and TikTok remain pending
owner/app setup. There is still no autonomous publishing.

**Phase 5 (publishing) code complete behind gates; Phase 6 (Creative Studio) planned next.**
The real publisher service + YouTube/IG/TikTok adapters exist behind owner approval (missing creds
return "not configured"; no autonomous publishing). `python -m pytest` → **191 passing**.

**2026-06-28 — Endpoint audit done (docs only, no features built).** Full endpoint vision + honest
status: `architecture/MASTER_ENDPOINT_RUBRIC.md` (+ `BUILD_GAP_ANALYSIS.md`, `CREATIVE_STUDIO_PLAN.md`,
`DEPARTMENT_SKILL_MAP.md`, `PLUGIN_PROVIDER_MAP.md`). ~55–60% of the endpoint vision built. Biggest gap =
**dashboard-native Creative Studio (video + thumbnail editing)**; recommended as Phase 6 (plan-first,
FFmpeg/MoviePy/Pillow — open-source, no paid lock-in, DeepSeek stays default).

**Also live since the last DNA refresh:** Sports Data Hub (ESPN + API-Football, cache, health, Telegram
alerts, agent-grounding), dashboard redesign (16 sections, login + Telegram 2FA), real Gmail email
reports — all deployed.

**2026-06-30 — Phase 6 Creative Studio V1a + V1b + V1c BUILT & DEPLOYED.** `creative/` (VideoProject
model, store, FFmpeg/Pillow/SRT providers, CLI) + `dashboard/studio.py` (Creative Studio UI: preview,
clip reorder/trim, caption edit, thumbnail, render draft, **AI revision via DeepSeek**, **compliance
re-check on render**, **Submit for review** → Approvals queue → scheduler → gated publisher). FFmpeg +
Pillow installed on the VPS; the full V1a→V1c flow (real DeepSeek title rewrite → render → compliance →
submit) was verified end-to-end on the server. Renders are local drafts; nothing publishes without owner
approval + the separate gated publisher. `python -m pytest` → **191 passing**.

Next options: V2 creative (Whisper auto-captions, FFmpeg.wasm scrubbing, Remotion templates) or build out
remaining departments (Creative/Marketing/Community/Commerce/Tech-Scout, Knowledge Library, skill packs).

**2026-06-30 (later) — breadth + V2 captions + YouTube bridge.** Built: (1) **Knowledge Library**
(`knowledge_library/`: file-based store + keyword search + CLI), (2) **department skill packs**
(`skills/packs.py`: 7 new draft-only skills, allowlisted; `DEPARTMENT_PACKS` map) + 5 new departments +
Knowledge Library in `AGENT_DIRECTORY`, (3) **Whisper auto-captions** (`creative/providers/whisper_captions.py`
+ studio `auto_caption`), (4) **Studio→YouTube bridge** (`PublishingService._post_from_item` attaches the
rendered video + title to a `video_project` review item). **FFmpeg.wasm + Remotion deferred** (heavy deps).
`python -m pytest` -> **184 passing**. YouTube credentials are now configured; Instagram/TikTok remain pending setup.

**2026-07-01 - live dashboard workflow QA + fixes.**
- YouTube OAuth is configured and verified against the correct **PlatinumClips** channel.
- Live private uploads already verified in YouTube Studio: `qmEb-5n3Ai8` (local verification) and
  `sGQ-azXJRrw` (VPS verification). No new upload was created during this QA pass.
- Fixed Ask Hermes draft-only routing: "do not publish" no longer creates orphaned `publish_content`
  actions. Content drafts, including compliance-warning drafts, enter the Review queue instead of
  standalone action approvals.
- Installed `python3-pil` on the VPS and tracked `Pillow>=10.0` in requirements. Creative Studio smoke on
  the VPS passes: demo -> render -> thumbnail -> previews -> no orphaned actions -> nothing published.
- Added Publishing History UI backed by the append-only server publish log.
- Browser QA prompt created review item `rv-2026-07-01-28494590` (`ready_for_owner_review`, published=False).
  It used live sports data context and did not publish.
- Remaining product gap: Hermes creates a review text draft, not a renderable Creative Studio video project.
  Existing soccer Studio project `vproj-20260630-3b406d28` has a thumbnail but cannot render because
  `assets/clip1.mp4` is missing. A UI-created demo project `vproj-20260701-bb653a7e` renders, but the
  output is generic dark background + caption, not a soccer highlight-style video.

## Current Working Module
`publishing/` adapters/service, `agents/social_publishing_agent.py`, `dashboard/{data,server,app}.py`, and `review/models.py`.

## Completed Files (Phase 4, 2026-06-09)
**Providers:** `providers/{__init__,deepseek_provider,nemotron_provider,model_router}.py`
**Orchestration:** `orchestration/{__init__,__main__,state,journal,routes,langgraph_app}.py`
**Approval:** `approval/{__init__,approval_queue,cli,__main__}.py`
**Agents:** `agents/{jarvis,worker_base,research_agent,content_agent,coding_agent,compliance_agent,openclaw_skill_agent,nemotron_reasoning_agent}.py`; updated `agents/hermes.py`
**Config:** `config/{model_budget.json,openclaw_allowlist.json,project_context.json}`
**Tests:** `tests/{_phase4_helpers,test_phase4_providers,test_phase4_cost,test_phase4_openclaw,test_phase4_routing,test_phase4_approval,test_phase4_graph}.py`
**Other:** `scripts/smoke_phase4.py`, `logs/agent_journal.jsonl`, `reports/approvals/.gitkeep`
**Edited:** `core/paths.py`, `main.py` is unchanged for Phase 1-3, `.env`/`.env.example` (NEMOTRON_*), `.gitignore`, `requirements.txt`, docs.

## Completed Files (Phase 5, 2026-06-28)
**Publishing:** `publishing/{__init__,base,http,youtube,instagram,tiktok,service}.py`
**Dashboard/review wiring:** `dashboard/{data,server,app}.py`, `agents/social_publishing_agent.py`, `review/models.py`, `.gitignore`, `reports/posts/.gitkeep`
**Tests:** `tests/test_publishing.py` plus existing dashboard/review safety suites.

## Broken Files
None.

## Known Bugs / Gaps
- Ask Hermes -> Approvals works for text/video-draft copy, but does **not** create a renderable Creative Studio project.
- Creative Studio can render projects with present media, but older project `vproj-20260630-3b406d28`
  has missing media (`assets/clip1.mp4`) and fails preflight clearly.
- Publishing History now shows both private YouTube verification uploads after backfilling the local
  verification record into the VPS publish log.

## Current Blockers
No deployment blockers. Product blocker: real prompt-matched video creation needs a safe media/source
pipeline and Hermes -> Creative Studio project wiring.

## API Keys Needed
Instagram Graph (`IG_ACCESS_TOKEN`, `IG_BUSINESS_ID`) and TikTok (`TIKTOK_ACCESS_TOKEN`) are still needed
for live platform workflows. YouTube OAuth, DeepSeek, Telegram, email, and sports keys are handled on the VPS.

## Owner Actions Needed
Do not approve public publishing yet. Instagram/TikTok setup remains pending. For Creative Studio, decide
whether Sportsverse should use generated/licensed soccer-safe visuals, owner-uploaded clips, or
template-only commentary videos for the next renderable-video version.

## Last Successful Test
`2026-07-01` - focused local suite:
`python -m pytest tests/test_phase4_approval.py tests/test_phase4_graph.py tests/test_dashboard_workflow.py tests/test_dashboard_ui.py tests/test_publishing.py -q` -> **39 passed**.
VPS smoke: `python3 scripts/smoke_studio.py` -> **ALL PASS**.

## Next Coding Task
Wire Hermes video prompts into Creative Studio projects with safe source media, then render a prompt-matched
30-second soccer draft in-dashboard. Keep Publishing gated; do not auto-upload.
