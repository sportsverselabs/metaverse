# API Keys & Environment Variables Needed

> The single live list of every secret/credential the project needs, and when.
> Mirror each item into `.env.example`. Never put real values here.
> Last updated: 2026-06-08

---

## Right now (Phase 0): NONE

The foundation needs **zero** API keys. You can ignore this entire list until Phase 1+.

---

## Environment variables (template lives in `.env.example`)

| Variable | Purpose | Needed when | Status | How owner gets it |
|---|---|---|---|---|
| `SPORTSVERSE_ENV` | local/vps/production switch | Phase 1 | not yet | set manually (no account) |
| `LOG_LEVEL` | logging verbosity | Phase 1 | not yet | set manually (no account) |
| `LLM_MODE` | `mock` (default, offline) or `live` (real calls) | to enable real AI | optional | set manually (no account) |
| `ANTHROPIC_API_KEY` | call Claude models via API | if `LLM_MODE=live` + anthropic | not yet | console.anthropic.com → API keys |
| `OPENAI_API_KEY` | call OpenAI models via API | if `LLM_MODE=live` + openai | not yet | platform.openai.com → API keys |
| `DEEPSEEK_API_KEY` | call DeepSeek models via API | if `LLM_MODE=live` + deepseek | not yet | platform.deepseek.com → API keys |
| `TELEGRAM_BOT_TOKEN` | Telegram bot messaging | if chat automation used | not yet | Telegram → @BotFather |
| `TELEGRAM_CHAT_ID` | target chat for the bot | with Telegram | not yet | from the bot/chat |
| `EMAIL_ADDRESS` | sending email | if system sends email | not yet | existing email account |
| `EMAIL_APP_PASSWORD` | email app password | with email sending | not yet | email provider security settings |
| `SMTP_HOST` / `SMTP_PORT` | email server | with email sending | not yet | email provider docs |
| `SPORTS_DATA_API_KEY` | sports data feed | when a data source chosen | not yet | TBD — provider not chosen |
| `SPORTS_DATA_BASE_URL` | sports data endpoint | with sports data | not yet | provider docs |
| `DATABASE_URL` | persistent storage | when DB added | not yet | chosen DB provider |
| `VPS_HOST` / `VPS_USER` | deployment target | Phase 5 (deploy) | not yet | VPS provider dashboard |

---

## Process when a new key becomes needed

1. Add the variable to `.env.example` (placeholder only).
2. Add a row to the table above with purpose + how to get it.
3. Add a beginner-friendly task to `OWNER_ACTION_REQUIRED.md`.
4. Tell the owner exactly when it's needed — don't request keys early.

---

## Security reminders

- Real values go **only** in the local `.env` (gitignored). Never here, never in code.
- Never log or print key values.
- If a key is ever exposed, rotate it immediately and note it in `security/security_policy.md`.
