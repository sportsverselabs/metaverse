# Claude Handoff - Phase 5 Social Platform Setup Pause

> Paste this file to Claude Code before resuming Phase 5 social publishing setup.
> This handoff records where the live platform account/app setup paused so project
> development can continue without reopening the same portal loops. It contains no
> platform secrets, tokens, VPS IPs, SSH keys, or passwords.

## Current Project Baseline

- Repo: `C:\Users\kjlun\Kamal's_Project\sportsverse-os`
- Current implementation baseline: commit `4091f7d Add owner-gated Phase 5 publishing`
- The Phase 5 publishing code is already implemented and committed:
  - `publishing/` package with YouTube, Instagram, and TikTok adapters
  - approval-gated `PublishingService`
  - dashboard Publishing connection state and explicit publish action
  - offline publishing tests
- Safety invariant remains unchanged: no autonomous publishing. All real posts must be
  explicitly owner-approved, and first platform runs must be private/draft/test-mode.
- Related docs:
  - `reports/handoff/PHASE5_CODEX_HANDOFF.md`
  - `docs/PHASE5_SETUP.md`
  - `docs/DASHBOARD_GUIDE.md`
  - `docs/MASTER_AUDIT.md`

## What To Avoid Rebuilding

Do not rebuild the publishing adapters or dashboard wiring from scratch. The active
work is now credential/account completion and final platform verification. Keep the
existing owner-gated design and do not move publishing into the autonomous execution
graph.

## YouTube Status

State: mostly wired, ready for cautious private-upload verification.

Completed:
- Google Cloud project created: `sportsverse-os`
- YouTube Data API enabled
- OAuth consent/app flow completed for YouTube upload scope
- Desktop OAuth client created
- One-time OAuth callback completed locally
- Refresh token was generated and stored outside git in local ignored config
- `secrets/youtube/client_secret.json` exists locally and is intentionally not for git
- Code supports private upload first through the YouTube adapter

Still needed:
- Verify the server/VPS environment has the YouTube env keys before claiming production readiness.
- Run the first real upload only from an explicitly approved dashboard item and keep it private.
- Do not print or commit `YOUTUBE_CLIENT_SECRET`, `YOUTUBE_REFRESH_TOKEN`, or client JSON.

Suggested next check:
- In the repo, run the offline test suite first.
- Then use the dashboard Publishing page to confirm YouTube shows connected in the environment being used.

## Facebook / Meta / Instagram Status

State: partially set up; paused because the Instagram OAuth/token flow became unreliable.

Completed:
- Meta developer registration flow was started/completed enough to create an app.
- Meta app exists for the Instagram Business setup:
  - Meta app ID observed: `1347369264184420`
  - Instagram app ID observed: `1499951475264798`
- Instagram account was created/logged in for Sportsverse:
  - Account username observed during setup: `sportsverse_media`
- User approved Sportsverse naming variants during setup.
- Instagram professional/business conversion flow was attempted and appeared to complete enough
  to return to the Meta developer setup.
- Tester/authorization acceptance was attempted through Instagram/Meta consent screens.
- IG user/business identifier observed in OAuth state: `17841414374842626`

Paused/blocker:
- Token generation repeatedly looped through Instagram login/consent and hit an Instagram/Meta
  OAuth failure path. The user chose to table Instagram and try again later.
- No reliable long-lived Instagram access token was captured or stored.
- Do not treat Instagram as configured until `IG_ACCESS_TOKEN`, `IG_BUSINESS_ID`, and, if needed,
  `FB_PAGE_ID` are deliberately obtained and placed server-side only.

Still needed next time:
- Revisit Meta Developer app dashboard.
- Confirm whether the IG account is business/creator and whether it is linked to a Facebook Page.
- Generate a long-lived Instagram token with required content publishing permission for test mode.
- Store secrets only in ignored `.env` / VPS env.
- Keep `IG_ALLOW_PUBLIC_PUBLISH` unset/false until the owner explicitly approves public posting
  and Meta permissions are verified.

Important note:
- Do not create another Instagram account unless the owner explicitly asks. Continue with the
  existing `sportsverse_media` account unless Meta proves it is unusable.

## TikTok Status

State: app draft is almost ready for review, but paused on TikTok's native file-picker uploads.

Completed:
- TikTok Developer app created:
  - App URL: `https://developers.tiktok.com/app/7656541492202391553/pending`
  - App name: `Sportsverse Publishing`
  - Ownership: Individual
  - Type/category: `Sports`
  - Status: Draft
- Domain property verified:
  - `sportsversenews.com`
- Hostinger DNS had TikTok verification TXT records added and propagation was verified.
- Public legal/callback pages are live:
  - `https://sportsversenews.com/privacy.html`
  - `https://sportsversenews.com/terms.html`
  - `https://sportsversenews.com/oauth/tiktok/callback/`
- TikTok products/scopes added:
  - Login Kit
  - Content Posting API
  - `user.info.basic`
  - `video.upload`
- Redirect URI set:
  - `https://sportsversenews.com/oauth/tiktok/callback/`
- Direct Post toggle was not enabled; keep TikTok in draft/inbox flow.
- Review explanation filled:
  - Sportsverse uses Login Kit so the owner can authorize TikTok access.
  - Content Posting API uploads owner-approved sports videos as TikTok drafts after dashboard approval.
  - No autonomous publishing.
- The extra blank Redirect URI row was removed; that validation error is fixed.

Current blocker:
- TikTok still shows exactly two remaining validation errors:
  - `App icon is required`
  - `Please upload at least one video`
- The in-app browser automation could not attach files through TikTok's native file picker.

Generated files to upload manually:
- Icon:
  - `C:\Users\kjlun\OneDrive\Documents\New project\.tiktok_setup\sportsverse-tiktok-icon.png`
- Demo review video:
  - `C:\Users\kjlun\OneDrive\Documents\New project\.tiktok_setup\sportsverse-tiktok-demo.mp4`

What to do next time:
1. Open the TikTok app draft page.
2. Upload the icon PNG in App details.
3. Upload the MP4 under App review demo video.
4. Click Save.
5. Verify the form no longer reports errors.
6. Do not submit for review without explicit owner approval at action time.
7. After review readiness, capture TikTok client key/secret and complete OAuth token setup without printing secrets.

Important TikTok implementation note:
- The adapter uses the draft/inbox-style Content Posting API path for `video.upload`.
- Do not attempt direct public posting before TikTok review/audit.

## Current Recommended Development Direction

Since social portal setup is paused, continue useful Sportsverse development without blocking on it:

- Keep building dashboard, review, scheduling, video review, analytics, and content workflows.
- Treat social publishing platforms as "pending owner portal completion" except YouTube local setup.
- Keep all publish actions guarded by owner approval and platform configured checks.
- Improve user-facing status messages so "not configured" is explicit and not mistaken for a failure.
- Continue tests and docs updates as normal.

## Verification Before Resuming

Run these before making new publishing changes:

```powershell
cd "C:\Users\kjlun\Kamal's_Project\sportsverse-os"
git status --short
python -m pytest
```

Expected baseline from last coding pass:
- Repo was clean after commit `4091f7d`.
- Full suite previously passed with 134 tests.

## Secret Handling Reminder

Never paste, print, commit, screenshot, or log:
- YouTube client secret / refresh token
- Instagram long-lived token
- TikTok client secret / access token / refresh token
- VPS SSH details or IP
- Any `.env` contents

Use only server-side ignored env files and the existing `config.secret(...)` pattern.
