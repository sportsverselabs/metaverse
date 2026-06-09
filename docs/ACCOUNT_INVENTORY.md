# SportVerse Labs — Account & Credential Inventory

Everything the system needs, where it goes, and current status. **Secrets live only in `.env`
(gitignored). Never commit or paste them into chat.**

| # | Item | Where it goes | Needed for | Status |
|---|---|---|---|---|
| 1 | Business email `sportverselabs@gmail.com` | account / notifications | identity | ✅ provided |
| 1b | YouTube channel `@PlatinumClips_SV` | publishing target (Phase 5) | brand | ✅ provided |
| 2 | DeepSeek API key | `.env` `DEEPSEEK_API_KEY` | live AI (default) | ✅ set & verified |
| 3 | Telegram bot token | `.env` `TELEGRAM_BOT_TOKEN` | Telegram control | ⏳ needed |
| 4 | Telegram chat id | `.env` `TELEGRAM_CHAT_ID` | restrict control to you | ⏳ needed |
| 5 | GitHub repo URL (**new account**) | `scripts/backup_github.sh` arg | code backup | ⏳ needed |
| 6 | GitHub token (if private) | git credential helper | push to private repo | ⏳ if private |
| 7 | Hostinger VPS IP (**new VPS**) | `.env` `VPS_HOST` (gitignored; not committed) | deployment | ✅ provided |
| 8 | VPS username (`root`) + SSH login | SSH (owner-side) | deployment | ✅ provided |
| 9 | Hostinger DNS access | Hostinger panel | connect domain | ⏳ needed |
| 10 | Nemotron API key + base URL | `.env` `NEMOTRON_*` | optional hard reasoning | ⚪ optional (off) |
| 11 | YouTube API credentials | `.env` (Phase 5) | publishing | 🔒 Phase 5 |
| 12 | Instagram/TikTok API creds | `.env` (Phase 5) | publishing | 🔒 Phase 5 |

## How to get the ones needed now
- **Telegram bot token:** Telegram → @BotFather → `/newbot` → copy token → `.env`.
- **Telegram chat id:** message @userinfobot (or the bot will report it) → `.env`.
- **GitHub repo:** create an empty repo on github.com → copy its URL.
- **VPS IP / SSH:** Hostinger panel → VPS → note IP + your login.

## Rules
- Never print secrets to logs (the Security Agent scans for leaks).
- Never commit `.env` (backup script refuses if it's tracked).
- Rotate any key that is ever exposed.
