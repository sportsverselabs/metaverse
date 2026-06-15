# Phase 5 — Live Publishing Setup (owner step-by-step)

Phase 5 connects real platforms so Sportsverse can send email and post to YouTube / Instagram / TikTok.
**You** do the account/portal steps below (they're tied to your identity). **The agent** wires each
credential into the system. **Safety stays on:** every post still goes through **Approvals** — you click
Approve before anything publishes, and where a platform allows it we start in **private/draft** mode first.

Do them in this order — easiest + highest value first:

| Order | Platform | Difficulty | What it unlocks |
|-------|----------|------------|-----------------|
| 1 | **Email (Gmail)** | Easy (~10 min) | Real daily/weekly reports + alerts to your inbox |
| 2 | **YouTube** | Medium (~30 min) | Upload videos to @PlatinumClips_SV |
| 3 | **Instagram** | Hard (needs Meta app review) | Post Reels/photos |
| 4 | **TikTok** | Hardest (starts in draft only) | Post videos (draft until app audit) |

---

## 1. Email (Gmail App Password) — DO THIS FIRST

Account: **sportsverseceo@gmail.com**

1. Sign in to that Gmail. Go to **myaccount.google.com → Security**.
2. Turn on **2-Step Verification** if it isn't already (required for app passwords).
3. Back in **Security**, search **"App passwords"** (or go to myaccount.google.com/apppasswords).
4. Create one — name it **"Sportsverse"**. Google shows a **16-character code** (like `abcd efgh ijkl mnop`).
5. **Give me two things** (in chat or to your developer): the email address and that 16-char code
   (remove the spaces). I add them to the server `.env` as `EMAIL_ADDRESS` + `EMAIL_APP_PASSWORD`.
6. Done — email reports/alerts go live. (Today the email module is dry-run; this flips it on.)

---

## 2. YouTube (Data API v3 — uploads)

Channel: **@PlatinumClips_SV**

1. Go to **console.cloud.google.com** → create a project named **Sportsverse**.
2. **APIs & Services → Library** → search **"YouTube Data API v3"** → **Enable**.
3. **APIs & Services → OAuth consent screen**:
   - User type **External** → fill App name (Sportsverse), your support email, developer email.
   - Add scope **`.../auth/youtube.upload`**.
   - Under **Test users**, add the Google account that owns the channel.
4. **APIs & Services → Credentials → Create credentials → OAuth client ID** → type **Desktop app** →
   **Download JSON** (`client_secret_….json`).
5. **Send me that JSON** (or paste its contents). The **first** upload needs a one-time browser
   "Allow" — I'll give you a link; you sign in with the channel's Google account and click Allow.
   That creates a saved refresh token; no clicking after that.

Notes (honest): API uploads default to **private** until your app is verified — fine for a small channel
(we'd flip each video public after your approval). Quota is ~6 uploads/day, plenty to start.

---

## 3. Instagram (Graph API — Reels/photos)

Requirements: your IG must be a **Business or Creator** account **linked to a Facebook Page**.

1. In the **Instagram app**: Settings → **Account type and tools → Switch to professional** (Business/Creator).
2. **Link it to a Facebook Page** (create a Page if you don't have one).
3. Go to **developers.facebook.com** → **Create App** → type **Business**.
4. Add the **Instagram** / **Instagram Graph API** product to the app.
5. Generate a **long-lived access token** and find your **Instagram Business account ID**
   (via the Graph API tools). **Send me:** the IG Business account ID, the Facebook Page ID, and the token.
6. **App Review:** to publish to anything beyond your own test account, Meta requires review for the
   **`instagram_content_publish`** permission. We can run in test mode first, then submit for review.

Honest: this is the fiddliest one (Meta app review). We can wire it and test on your own account before review.

---

## 4. TikTok (Content Posting API)

1. Go to **developers.tiktok.com** → register as a developer → **create an app**.
2. Add the **Content Posting API** product.
3. **Send me:** the app's **client key** and **client secret**. You'll do a one-time OAuth "authorize"
   to grant your TikTok account (I'll give you the link).
4. **Audit:** until TikTok audits your app, posts can only be created as **private / draft (SELF_ONLY)** —
   the video lands in your TikTok drafts and you publish it manually in the app. After audit, direct
   public posting can be enabled.

Honest: TikTok is the most restrictive — plan to start in **draft mode** and publish from your phone.

---

## What the agent does once you hand over each credential

1. Adds the secret to the server `.env` (never logged, never committed).
2. Builds a small publishing adapter for that platform **behind the existing approval gate**.
3. Flips that platform in the **Publishing** dashboard section from *"needs owner setup"* → *"connected"*.
4. First real post runs in **private/draft** where the platform supports it, so you can sanity-check
   before anything goes public.

**Unchanged safety rule:** nothing auto-posts. Content → **Approvals** → you click **Approve** → it posts.

---

## Quick reference — what to send me, per platform

- **Email:** `sportsverseceo@gmail.com` + 16-char App Password
- **YouTube:** the OAuth `client_secret….json` (then click "Allow" once)
- **Instagram:** IG Business account ID + Facebook Page ID + long-lived access token
- **TikTok:** client key + client secret (then "authorize" once)

> Send secrets carefully. Best is to paste them when you're ready to wire that one platform, not all at once.
