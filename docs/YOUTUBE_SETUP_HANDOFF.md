# YouTube Setup Handoff — get Sportsverse uploading (private) to PlatinumClips

> For Codex (with a browser) **or** the owner. Goal: create a YouTube OAuth credential and mint a
> refresh token so the Creative Studio can upload approved videos **as private** for owner review.
> Account: **sportverselabs@gmail.com** · Channel: **PlatinumClips**.
>
> Our publisher (`publishing/youtube.py`) needs exactly three values in `.env`:
> `YOUTUBE_CLIENT_ID`, `YOUTUBE_CLIENT_SECRET`, `YOUTUBE_REFRESH_TOKEN`. There is a helper script that
> produces all three: `scripts/youtube_authorize.py`. Nothing publishes automatically — uploads default
> to **private** and still go through the dashboard approval + explicit Publish action.

---

## Part A — Google Cloud Console (browser; signed in as sportverselabs@gmail.com)

1. Go to **https://console.cloud.google.com/** and sign in as **sportverselabs@gmail.com**.
2. **Create a project**: top project dropdown → **New Project** → name **Sportsverse** → Create → select it.
3. **Enable the API**: search bar → "**YouTube Data API v3**" → **Enable**
   (or: APIs & Services → Library → search → Enable).
4. **OAuth consent screen** (APIs & Services → OAuth consent screen):
   - User type: **External** → Create.
   - App name: **Sportsverse**; User support email: **sportverselabs@gmail.com**; Developer contact: **sportverselabs@gmail.com** → Save and Continue.
   - **Scopes**: Add → search `youtube.upload` → check **.../auth/youtube.upload** → Update → Save and Continue.
   - **Test users**: Add users → **sportverselabs@gmail.com** → Save and Continue. (Leave the app in
     "Testing"; a test user can authorize without full Google verification.)
5. **Create the OAuth client** (APIs & Services → Credentials → Create credentials → **OAuth client ID**):
   - Application type: **Desktop app** (important — the helper uses a loopback redirect).
   - Name: **Sportsverse Desktop** → Create.
   - In the dialog, click **Download JSON** → save it as `client_secret.json`.
   - ⚠️ This file is a **secret** — do not commit it, do not paste it in a public channel.

## Part B — Mint the refresh token (one command)

On any machine with a browser (your laptop is easiest), in the repo:

```bash
python scripts/youtube_authorize.py --client-secrets /path/to/client_secret.json
```

- A browser tab opens the Google consent screen → sign in as **sportverselabs@gmail.com** → **Allow**.
- The script captures the result on a local loopback port and prints three lines:
  ```
  YOUTUBE_CLIENT_ID=...
  YOUTUBE_CLIENT_SECRET=...
  YOUTUBE_REFRESH_TOKEN=...
  ```
- If you run it **on the VPS** (no desktop browser), add `--write` to drop them straight into `.env`;
  otherwise copy the three lines and hand them to the developer/agent to put in the VPS `.env`.

Notes:
- You only do this **once**; the refresh token is long-lived.
- If it says "No refresh_token returned", revoke the app at
  https://myaccount.google.com/permissions and re-run (the script already forces `prompt=consent`).

## Part C — Install on the server (developer/agent)

Add the three lines to **`/root/metaverse/.env`** (server-side only, never committed), then:
```bash
cd /root/metaverse && systemctl restart sportverse-dashboard
```
The dashboard **Publishing** page should now show **YouTube: connected**.

## Part D — First real upload (owner, gated)

1. In the dashboard **Creative Studio**: render a draft video → **Submit for review** (runs compliance).
2. In **Approvals**: approve it.
3. In **Publishing** (or the item's Publish action): **Publish to YouTube** with visibility **private**.
4. The video appears in the PlatinumClips channel as **Private** → review it in YouTube Studio →
   make it public yourself when happy. (Quota ≈ 6 uploads/day; uploads stay private until you flip them.)

## What to hand back to the agent
Either: the **3 `.env` lines** from Part B, or confirmation that you ran `--write` on the VPS.
That's the only blocker — once those are in `.env`, the full draft→review→approve→publish loop is live.

---
**Safety (unchanged):** no auto-publishing; uploads default to **private**; every publish needs an
explicit owner approval + Publish click; secrets live only in `.env`, never logged or committed.
