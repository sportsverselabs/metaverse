# HANDOFF — Phase 5: Live Publishing (for Codex / next coding agent)

> Paste this whole file to the next agent. It is scoped to **Phase 5 = real publishing**
> (YouTube, Instagram, TikTok) behind the existing approval gate. For full system context and
> **VPS/SSH/GitHub access details**, also read `reports/handoff/CODEX_HANDOFF.md` (same folder).

---

## 1. What Sportsverse is (1 paragraph)
A low-cost, gated, human-in-the-loop AI system running a sports/news brand. Brand **"Sportsverse"**,
domain **sportsversenews.com** (NOT "sportsversusnews.com" — that's a recurring typo), owner email
sportsverseceo@gmail.com, YouTube **@PlatinumClips_SV**. **Hermes** routes tasks; **Jarvis** is the
chat interface; workers draft content; **nothing publishes/spends/installs without explicit owner
approval.** Python 3.9+ (3.13 local / 3.12 VPS), stdlib-first, only hard dep `openai` (for DeepSeek).
`python -m pytest` must stay green (currently **125 passing**).

## 2. What is ALREADY built and live (do not rebuild)
- Core OS: Hermes/Jarvis, LangGraph (+ built-in fallback), model router (DeepSeek default, Nemotron for
  complex), OpenClaw skill registry, approval + review (8 status gates) + scheduler.
- **Dashboard LIVE** (login + Telegram 2FA), 16 sections incl. **Publishing** and **Video Review**
  (both currently placeholders / "needs owner setup"). https://dashboard.sportsversenews.com
- **Email LIVE** (`integrations/email_report.py`, real Gmail SMTP) — copy this pattern.
- **Sports Data Hub LIVE** (`sports/`: ESPN + API-Football, cache, health, Telegram alerts) — and it's
  the **reference architecture** for Phase 5 adapters (provider client + server-side key + defensive I/O).
- Telegram bot live; GitHub backup; full VPS deploy (nginx + SSL + systemd).

## 3. Phase 5 GOAL
Turn approved content drafts into **real posts** on YouTube, Instagram, and TikTok — **only after owner
approval**, and **starting in private/draft mode** where each platform allows it. Flip the dashboard
**Publishing** section connections from "needs owner setup" → "connected", and let an
owner-approved+scheduled review item actually publish (status → `STATUS_PUBLISHED`).

## 4. The safety invariants you MUST NOT break (these are the whole point)
1. **No autonomous publishing.** A post happens only when the owner has explicitly approved that specific
   item. `execution_agent` (`orchestration/routes.py:node_execution_agent`) must remain a no-op for
   external actions — publishing happens via a **separate, explicitly-invoked publisher**, not the graph.
2. **Draft/private first.** Where a platform supports it (YouTube `privacyStatus=private`, TikTok
   `SELF_ONLY`/draft, IG test users), the first real post must be private/draft for owner verification.
3. **Secrets:** all platform creds live in `.env` only, used **server-side only**, **never logged**,
   **never committed** (`.env` is gitignored — verify before every commit).
4. **Compliance + review gates stay in front of publishing.** Only items at `STATUS_OWNER_APPROVED` /
   `STATUS_SCHEDULED` may be published; publishing sets `STATUS_PUBLISHED`.
5. Keep the mock/dry-run fallback: if creds are missing, the publisher returns "not configured" (like
   `EmailReporter`/`SocialPublishingAgent.publish()` do today) — never a fake success.
6. After every change: `python -m pytest` stays green; update continuity docs.

## 5. Current publishing-related code (your starting points)
- `agents/social_publishing_agent.py` — **skeleton**. `prepare(content, platform, ...)` builds a post
  dict; `publish(post, approved, live_capability)` currently **always refuses** ("Phase 5"). This is the
  seam to implement: when `approved` and a real adapter is configured, call the adapter.
- `orchestration/routes.py` — `node_execution_agent` (NEVER publishes), `_queue_into_review()` puts
  compliance-passing content into the review surface. Leave the graph's no-op guarantee intact.
- `review/models.py` — statuses incl. `STATUS_OWNER_APPROVED`, `STATUS_SCHEDULED`, `STATUS_PUBLISHED`.
- `review/` + `scheduler/` — the approve/schedule pipeline. Find where `STATUS_SCHEDULED` is set and add
  a **publisher step** that, on owner action, calls the platform adapter and sets `STATUS_PUBLISHED`
  (with the returned post id/url) — or `STATUS_REVISION`/error on failure.
- `dashboard/data.py:publishing()` — returns per-platform connection status; update it to read real
  adapter `.configured` state. `dashboard/app.py:_r_publishing` renders it.
- `docs/PHASE5_SETUP.md` — the **owner-facing** credential steps per platform (already written). The
  owner provides creds; you wire them.

## 6. Recommended architecture (mirror `sports/` + `EmailReporter`)
Create `publishing/` (new package):
```
publishing/
  __init__.py
  base.py              # PublishResult dataclass + Publisher protocol: .configured, .publish(post)->PublishResult
  youtube.py           # YouTubePublisher  (OAuth refresh token; resumable upload; privacyStatus=private first)
  instagram.py         # InstagramPublisher (Graph API: create media container -> publish; test user first)
  tiktok.py            # TikTokPublisher    (Content Posting API; SELF_ONLY/draft until app audited)
  service.py           # PublishingService: picks adapter by platform, enforces approved=True, logs result
```
Rules per adapter:
- Read creds from `config.secret(...)`; expose `.configured: bool`. If not configured → `PublishResult(ok=False, reason="not configured")`.
- Inject an HTTP `fetch`/transport so tests run **offline** (same trick as `ESPNClient(fetch=...)`).
- Return `PublishResult(ok, platform, post_id, url, reason, dry_run)`. Never raise into the caller.
- Default to private/draft; expose an explicit `visibility` arg the owner controls from the dashboard.

Wire-up:
- `PublishingService.publish_review_item(item, platform, visibility)` — assert the item is owner-approved,
  call the adapter, on success set `STATUS_PUBLISHED` + store `post_id/url`, append to a publish log + journal.
- Dashboard **Publishing**: add per-platform "connected/needs setup" from adapter `.configured`, and on an
  approved item show a **Publish (private)** button → POST `/dashboard/action` action `publish`
  (add the handler in `dashboard/server.py`, with the existing "Are you sure?" confirm).
- **Video Review** section: add Download + "Upload edited version" + Approve/Reject (currently placeholder).

## 7. Per-platform notes (see `docs/PHASE5_SETUP.md` for the owner steps + what creds arrive)
- **YouTube (do first):** Data API v3. Owner gives OAuth `client_secret.json`; first run does a one-time
  consent to mint a **refresh token** (store in `.env` as `YOUTUBE_REFRESH_TOKEN`, plus client id/secret).
  Upload via resumable endpoint, `status.privacyStatus="private"`. Quota ~6 uploads/day.
- **Instagram:** Graph API. Needs IG **Business/Creator** linked to a FB Page; creds: long-lived token,
  IG business account id, FB page id. Flow: POST media container → POST media_publish. Full public posting
  needs Meta **App Review** (`instagram_content_publish`) — build + test on the owner's own account first.
- **TikTok:** Content Posting API. Creds: client key + secret + a user OAuth grant. Until app audit, posts
  must be **SELF_ONLY/draft** (land in the owner's TikTok drafts). Don't attempt public posting pre-audit.

## 8. Credentials the OWNER must provide (you cannot get these)
| Platform | Env keys (suggested) | Status |
|----------|----------------------|--------|
| YouTube | `YOUTUBE_CLIENT_ID`, `YOUTUBE_CLIENT_SECRET`, `YOUTUBE_REFRESH_TOKEN` | pending |
| Instagram | `IG_ACCESS_TOKEN`, `IG_BUSINESS_ID`, `FB_PAGE_ID` | pending |
| TikTok | `TIKTOK_CLIENT_KEY`, `TIKTOK_CLIENT_SECRET`, `TIKTOK_ACCESS_TOKEN` | pending |
Email, DeepSeek, Telegram, API-Football, dashboard creds are already set on the VPS `.env`.

## 9. Tests & deploy
- Add `tests/test_publishing.py` — fully offline (injected transport). Cover: not-configured → refuses;
  approved+configured → calls transport, returns post id; unapproved → refuses; visibility defaults to private.
- Keep the suite green (`python -m pytest`, currently 125).
- Deploy pattern (details/SSH in `CODEX_HANDOFF.md`): commit + push → on VPS `git pull` +
  `systemctl restart sportverse sportverse-dashboard`. Add new env keys to `/root/metaverse/.env`.
  Local PowerShell sandbox blocks `rm` on system paths and `\n` in `curl -w`; for VPS use
  `dangerouslyDisableSandbox: true` and avoid `rm`/`\n`.

## 10. Definition of done for Phase 5
- [ ] `publishing/` adapters for YouTube, Instagram, TikTok with offline tests.
- [ ] An owner-approved review item can be published from the dashboard (private/draft first) → `STATUS_PUBLISHED` with stored post id/url.
- [ ] Dashboard **Publishing** shows real per-platform connection status; **Video Review** has download/upload/approve.
- [ ] Telegram alert on publish success/failure (reuse `JarvisTelegramBot.send`).
- [ ] No secrets in logs/git; `execution_agent` still never auto-publishes; tests green; docs updated
      (`docs/PHASE5_SETUP.md` status, `CURRENT_STATUS.md`, `docs/MASTER_AUDIT.md`).

## 11. Read these (source of truth)
`reports/handoff/CODEX_HANDOFF.md` (VPS/SSH/GitHub access), `docs/PHASE5_SETUP.md` (owner cred steps),
`docs/MASTER_AUDIT.md` (honest status, ~82%), `docs/SPORTS_DATA_HUB.md` (architecture pattern to mirror),
`integrations/email_report.py` (real-send pattern), `docs/DASHBOARD_GUIDE.md`, `PROJECT_DNA.md`.
