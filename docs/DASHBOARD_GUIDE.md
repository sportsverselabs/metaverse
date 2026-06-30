# Sportsverse Dashboard Guide

Your private command center for running Sportsverse. This guide is written for the owner —
no coding needed. It is **honest**: where a feature isn't built yet, it says so plainly.

---

## 1. How to sign in

1. Go to **https://dashboard.sportsversenews.com**
2. Enter your **username** (`owner`) and your **password**.
3. A **6-digit code** is sent to your Telegram (`@Sportsversebot`). Enter it to finish signing in.
4. You're in. Your session stays valid for a while; **Logout** (top of the sidebar/menu) ends it.

**Security notes**
- The password is stored only as a one-way hash on the server — it is never shown or logged.
- The 2FA code expires after ~5 minutes and allows a few attempts, then you start over.
- Codes are never written to logs. If a code doesn't arrive, the Telegram bot may be down — see §5.
- Lost the password? It can be reset on the server with `scripts/set_dashboard_password.py --write`
  (a new one is generated and shown once). Ask your developer/agent to run it.

---

## 2. The 16 sections (what each does, and what's real vs. placeholder)

Honesty key: **✅ real** = live working data/actions · **🟡 functional** = works, limited ·
**⚪ placeholder** = screen exists but the feature needs setup/build (clearly labeled in-app).

| # | Section | Status | What it shows / does |
|---|---------|--------|----------------------|
| 1 | **Home** | ✅ real | System status of all components, pending approvals count, today's activity, errors/warnings, today's + month-to-date cost, your to-do list. |
| 2 | **Ask Hermes** | 🟡 functional | Type a request; it runs through Hermes → the agents (live DeepSeek). Returns a result. Does **not** publish anything — output is for your review. |
| 3 | **Approvals** | ✅ real | Pending content and actions. Buttons: **Approve**, **Request edit**, **Reject**, **Schedule**. Wired to the real review system. Approving ≠ publishing. |
| 4 | **Content Pipeline** | real | Counts of items at each stage: drafting -> waiting approval -> needs edit -> approved -> scheduled -> rejected -> published. Published only changes after the explicit Phase 5 publisher succeeds. |
| 5 | **Creative Studio** | 🟡 functional | Dashboard-native video editor. Preview a draft render, reorder/trim clips, edit captions, generate a thumbnail, and render a draft (local file only — **nothing publishes**). Approve / AI-revision arrive in V1c. Rendering needs FFmpeg on the server (installed). |
| 6 | **Publishing** | functional | Shows real platform connection status from server-side adapters. Owner-approved/scheduled items can be explicitly published to YouTube private, TikTok draft, or Instagram test/public-guarded flows once credentials exist. |
| 7 | **Analytics** | ⚪ placeholder | Shows only recorded data. Real views/likes/watch-time need platform API connections (Phase 5). |
| 8 | **Reports** | ✅ real | Daily and weekly summaries built from the system's own activity journal. |
| 9 | **Agents** | ✅ real | The full agent directory and each agent's purpose. |
| 10 | **Security** | ✅ real | Live self-scan findings (config/safety checks) with severity. |
| 11 | **Costs** | ✅ real | Month-to-date and today's estimated spend, plus monthly budget and per-task approval threshold. |
| 12 | **Backups** | ✅ real | GitHub backup safety check (whether code is safely backed up). |
| 13 | **Settings** | ✅ real | Non-secret settings (environment, LLM mode/provider, Nemotron on/off). **Secrets are never shown** — edit `.env` on the server to change keys. |
| 14 | **System Manual** | ✅ real | Links to all docs + the agent directory. |

---

## 3. The golden safety rules (built in — the dashboard cannot break them)

1. **Nothing publishes automatically.** Approving or scheduling an item does **not** post it.
   Phase 5 posting requires a separate dashboard Publish confirmation and server-side platform credentials. YouTube/TikTok start private/draft; Instagram public publishing remains separately disabled unless the owner enables it.
2. **Nothing spends above the budget threshold** without an approval gate (`config/model_budget.json`).
3. **OpenClaw skills are allowlisted only** (`config/openclaw_allowlist.json`).
4. **No secrets, passwords, API keys, or 2FA codes are ever logged or shown.**
5. **No production change happens without your approval.**

---

## 4. Typical daily flow

1. Open **Home** - check status (all green?), today's cost, and pending counts.
2. Go to **Approvals** — review each draft. **Approve**, **Request edit**, or **Reject**.
   Use **Schedule** to queue an approved item (still does not publish).
3. Use **Ask Hermes** to kick off research or drafting on demand.
4. Glance at **Costs** to stay within budget, and **Reports** for the daily/weekly recap.

---

## 5. Troubleshooting

| Symptom | Likely cause / fix |
|---------|--------------------|
| Login page won't load | Dashboard service down. On the VPS: `systemctl restart sportverse-dashboard`. |
| Password accepted but **no Telegram code** | Telegram bot down/misconfigured. Check `systemctl status sportverse` and that `TELEGRAM_BOT_TOKEN` + your chat id are in `.env`. |
| "Code expired / too many attempts" | Codes last ~5 min with limited tries. Just sign in again to get a fresh code. |
| A section shows "placeholder / needs owner setup" | That's intentional and honest — that feature isn't built/connected yet (see the table in §2). |
| Logged out unexpectedly | Session expired or the server restarted (sessions are in-memory). Sign in again. |

---

## 6. For the developer / next agent

- App: `dashboard/` — `server.py` (routes + session gating), `app.py` (pages + section renderers),
  `data.py` (per-section data). Auth: `auth/` — `passwords.py`, `sessions.py`, `twofa.py`, `service.py`.
- Service: `deployment/sportverse-dashboard.service` (runs `python -m dashboard` on `127.0.0.1:8787`).
- Nginx: `deployment/nginx_sportsverse_site.conf` — public site on apex/www (no auth),
  dashboard subdomain proxies to the app (**no** nginx basic auth; the app does login + 2FA).
- Creds: `scripts/set_dashboard_password.py --write` writes `DASH_USER` / `DASH_PASSWORD_HASH` /
  `SESSION_SECRET` into `.env` (hash + secret generated server-side; password shown once).
- Tests: `tests/test_auth.py`, `tests/test_dashboard_ui.py`. Run `python -m pytest` (keep it green).
