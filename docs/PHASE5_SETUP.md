# Phase 5 â€” Live Publishing Setup (owner step-by-step)

Phase 5 connects real platforms so Sportsverse can send email and post to YouTube / Instagram / TikTok.
**You** do the account/portal steps below (they're tied to your identity). **The agent** wires each
credential into the system. **Safety stays on:** every post still goes through **Approvals** â€” you click
Approve before anything publishes, and where a platform allows it we start in **private/draft** mode first.

Do them in this order â€” easiest + highest value first:

| Order | Platform | Difficulty | What it unlocks |
|-------|----------|------------|-----------------|
| 1 | **Email (Gmail)** | Easy (~10 min) | Real daily/weekly reports + alerts to your inbox |
| 2 | **YouTube** | Medium (~30 min) | Upload videos to @PlatinumClips_SV |
| 3 | **Instagram** | Hard (needs Meta app review) | Post Reels/photos |
| 4 | **TikTok** | Hardest (starts in draft only) | Post videos (draft until app audit) |

---

## Implementation status (2026-06-28)

The Phase 5 code path now exists behind the approval gate:
- `publishing/` contains YouTube, Instagram, and TikTok adapters with offline-tested transports.
- The dashboard Publishing page reads real configured/not-configured state from those adapters.
- Approved/scheduled review items can call the explicit dashboard Publish action; missing credentials return "not configured" instead of fake success.
- YouTube and TikTok default to private/draft-style visibility. Instagram public publishing remains guarded by `IG_ALLOW_PUBLIC_PUBLISH=true`.

Owner credentials are still required before any real platform post can succeed.

## 1. Email (Gmail App Password) â€” DO THIS FIRST

Account: **sportsverseceo@gmail.com**

1. Sign in to that Gmail. Go to **myaccount.google.com â†’ Security**.
2. Turn on **2-Step Verification** if it isn't already (required for app passwords).
3. Back in **Security**, search **"App passwords"** (or go to myaccount.google.com/apppasswords).
4. Create one â€” name it **"Sportsverse"**. Google shows a **16-character code** (like `abcd efgh ijkl mnop`).
5. **Give me two things** (in chat or to your developer): the email address and that 16-char code
   (remove the spaces). I add them to the server `.env` as `EMAIL_ADDRESS` + `EMAIL_APP_PASSWORD`.
6. Done â€” email reports/alerts go live. (Today the email module is dry-run; this flips it on.)

---

## 2. YouTube (Data API v3 â€” uploads)

Channel: **@PlatinumClips_SV**

1. Go to **console.cloud.google.com** â†’ create a project named **Sportsverse**.
2. **APIs & Services â†’ Library** â†’ search **"YouTube Data API v3"** â†’ **Enable**.
3. **APIs & Services â†’ OAuth consent screen**:
   - User type **External** â†’ fill App name (Sportsverse), your support email, developer email.
   - Add scope **`.../auth/youtube.upload`**.
   - Under **Test users**, add the Google account that owns the channel.
4. **APIs & Services â†’ Credentials â†’ Create credentials â†’ OAuth client ID** â†’ type **Desktop app** â†’
   **Download JSON** (`client_secret_â€¦.json`).
5. **Send me that JSON** (or paste its contents). The **first** upload needs a one-time browser
   "Allow" â€” I'll give you a link; you sign in with the channel's Google account and click Allow.
   That creates a saved refresh token; no clicking after that.

Notes (honest): API uploads default to **private** until your app is verified â€” fine for a small channel
(we'd flip each video public after your approval). Quota is ~6 uploads/day, plenty to start.

---

## 3. Instagram (Graph API â€” Reels/photos)

Requirements: your IG must be a **Business or Creator** account **linked to a Facebook Page**.

1. In the **Instagram app**: Settings â†’ **Account type and tools â†’ Switch to professional** (Business/Creator).
2. **Link it to a Facebook Page** (create a Page if you don't have one).
3. Go to **developers.facebook.com** â†’ **Create App** â†’ type **Business**.
4. Add the **Instagram** / **Instagram Graph API** product to the app.
5. Generate a **long-lived access token** and find your **Instagram Business account ID**
   (via the Graph API tools). **Send me:** the IG Business account ID, the Facebook Page ID, and the token.
6. **App Review:** to publish to anything beyond your own test account, Meta requires review for the
   **`instagram_content_publish`** permission. We can run in test mode first, then submit for review.

Honest: this is the fiddliest one (Meta app review). We can wire it and test on your own account before review.

---

## 4. TikTok (Content Posting API)

1. Go to **developers.tiktok.com** â†’ register as a developer â†’ **create an app**.
2. Add the **Content Posting API** product.
3. **Send me:** the app's **client key**, **client secret**, and saved **refresh token**. You'll do a one-time OAuth "authorize"
   to grant your TikTok account (I'll give you the link).
4. **Audit:** until TikTok audits your app, posts can only be created as **private / draft (SELF_ONLY)** â€”
   the video lands in your TikTok drafts and you publish it manually in the app. After audit, direct
   public posting can be enabled.

Honest: TikTok is the most restrictive â€” plan to start in **draft mode** and publish from your phone.

---

## What the agent does once you hand over each credential

1. Adds the secret to the server `.env` (never logged, never committed).
2. Builds a small publishing adapter for that platform **behind the existing approval gate**.
3. Flips that platform in the **Publishing** dashboard section from *"needs owner setup"* â†’ *"connected"*.
4. First real post runs in **private/draft** where the platform supports it, so you can sanity-check
   before anything goes public.

**Unchanged safety rule:** nothing auto-posts. Content â†’ **Approvals** â†’ you click **Approve** â†’ it posts.

---

## Quick reference â€” what to send me, per platform

- **Email:** `sportsverseceo@gmail.com` + 16-char App Password
- **YouTube:** the OAuth `client_secretâ€¦.json` (then click "Allow" once)
- **Instagram:** IG Business account ID + Facebook Page ID + long-lived access token
- **TikTok:** client key + client secret + refresh token (then "authorize" once)

> Send secrets carefully. Best is to paste them when you're ready to wire that one platform, not all at once.
