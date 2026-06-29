# CURRENT_STATUS.md

> Live snapshot of where the project is **right now**.
> Update this at the start and end of every coding session.

| Field | Value |
|---|---|
| Last updated | 2026-06-28 |
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
**Phase 5 (publishing) code complete behind gates; Phase 6 (Creative Studio) planned next.**
The real publisher service + YouTube/IG/TikTok adapters exist behind owner approval (missing creds
return "not configured"; no autonomous publishing). `python -m pytest` → **134 passing**.

**2026-06-28 — Endpoint audit done (docs only, no features built).** Full endpoint vision + honest
status: `architecture/MASTER_ENDPOINT_RUBRIC.md` (+ `BUILD_GAP_ANALYSIS.md`, `CREATIVE_STUDIO_PLAN.md`,
`DEPARTMENT_SKILL_MAP.md`, `PLUGIN_PROVIDER_MAP.md`). ~55–60% of the endpoint vision built. Biggest gap =
**dashboard-native Creative Studio (video + thumbnail editing)**; recommended as Phase 6 (plan-first,
FFmpeg/MoviePy/Pillow — open-source, no paid lock-in, DeepSeek stays default).

**Also live since the last DNA refresh:** Sports Data Hub (ESPN + API-Football, cache, health, Telegram
alerts, agent-grounding), dashboard redesign (16 sections, login + Telegram 2FA), real Gmail email
reports — all deployed.

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

## Known Bugs
None. (Fixed a Windows-console UTF-8 print issue in the Jarvis CLI.)

## Current Blockers
None.

## API Keys Needed
YouTube OAuth (`YOUTUBE_CLIENT_ID`, `YOUTUBE_CLIENT_SECRET`, `YOUTUBE_REFRESH_TOKEN`), Instagram Graph (`IG_ACCESS_TOKEN`, `IG_BUSINESS_ID`), and TikTok (`TIKTOK_ACCESS_TOKEN`) are still needed for live platform posting. DeepSeek, Telegram, email, and sports keys are already handled on the VPS.

## Owner Actions Needed
Provide the YouTube OAuth credentials first if YouTube private uploads should go live. Keep Instagram public publishing disabled until the owner has a test-account/app-review path and explicitly enables `IG_ALLOW_PUBLIC_PUBLISH=true`.

## Last Successful Test
`2026-06-28` - `python -m pytest` -> **131 passed** (exit 0).
Targeted Phase 5 check: `python -m pytest tests/test_publishing.py tests/test_phase5_ops.py tests/test_dashboard_ui.py tests/test_review.py tests/test_gates.py tests/test_phase5_agents.py` -> **39 passed**.

## Next Coding Task
Add real owner credentials to `.env`, perform the one-time YouTube OAuth refresh-token flow, then run the first dashboard-triggered YouTube upload in private mode.
