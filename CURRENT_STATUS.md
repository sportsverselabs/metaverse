# CURRENT_STATUS.md

> Live snapshot of where the project is **right now**.
> Update this at the start and end of every coding session.

| Field | Value |
|---|---|
| Last updated | 2026-06-10 |
| Updated by | Coding Agent (Claude Code / Opus 4.8) |

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
**Phase 4 — COMPLETE (+ follow-ups).** Hermes Multi-Agent Operating Core, plus: deepened
Compliance (real per-dimension checks) and orchestration→review-queue wiring. Phases 0–3 preserved.

## Current Working Module
`agents/compliance.py` (deepened checks), `orchestration/routes.py` (content drafts → review
surface), `core/console.py` (UTF-8 console for all CLIs).

## Completed Files (Phase 4, 2026-06-09)
**Providers:** `providers/{__init__,deepseek_provider,nemotron_provider,model_router}.py`
**Orchestration:** `orchestration/{__init__,__main__,state,journal,routes,langgraph_app}.py`
**Approval:** `approval/{__init__,approval_queue,cli,__main__}.py`
**Agents:** `agents/{jarvis,worker_base,research_agent,content_agent,coding_agent,compliance_agent,openclaw_skill_agent,nemotron_reasoning_agent}.py`; updated `agents/hermes.py`
**Config:** `config/{model_budget.json,openclaw_allowlist.json,project_context.json}`
**Tests:** `tests/{_phase4_helpers,test_phase4_providers,test_phase4_cost,test_phase4_openclaw,test_phase4_routing,test_phase4_approval,test_phase4_graph}.py`
**Other:** `scripts/smoke_phase4.py`, `logs/agent_journal.jsonl`, `reports/approvals/.gitkeep`
**Edited:** `core/paths.py`, `main.py` is unchanged for Phase 1-3, `.env`/`.env.example` (NEMOTRON_*), `.gitignore`, `requirements.txt`, docs.

## Broken Files
None.

## Known Bugs
None. (Fixed a Windows-console UTF-8 print issue in the Jarvis CLI.)

## Current Blockers
None.

## API Keys Needed
DeepSeek key in place + verified. Nemotron is OPTIONAL (disabled). LangGraph is OPTIONAL.

## Owner Actions Needed
None required. Optional:
- Try the core: `python -m orchestration "research trending football stories"`.
- Review gated approvals: `python -m approval list`.
- (Optional) `pip install langgraph` for the real engine; set `NEMOTRON_*` to enable Nemotron.

## Last Successful Test
`2026-06-09` — `python -m pytest` → **85 passed** (exit 0).
`python scripts/smoke_phase4.py` → routing + DeepSeek/Nemotron-fallback + compliance + gated
approvals + OpenClaw allowlist block + journaling; `any_published=False`.
**Live**: `python -m orchestration "draft a hype caption ..."` → DeepSeek → compliance →
**queued into the review surface** (`rv-...`), shown by `python -m review list`. All CLIs UTF-8-safe.

## Next Coding Task
See `NEXT_STEPS.md`: optionally enable LangGraph/Nemotron; expand which routes feed the review
queue; build per-platform compliance refinements. Phase 5 (real publisher) stays LOCKED until
the owner explicitly asks.
