# SportVerse Labs — Recovery Guide

The whole project is one portable folder. Recovery = restore the folder + recreate `.env`.

## Back up
- **Code (safe):** `bash scripts/backup_github.sh https://github.com/<you>/<repo>.git`
  (secrets excluded automatically).
- **Secrets:** keep a private, secure copy of `.env` OFF GitHub (password manager / encrypted note).
- **Runtime data** (drafts, schedule, journal, approvals) lives under `reports/`, `memory/store/`,
  `logs/` — gitignored. Copy these if you want to preserve in-flight work.

## Restore on a fresh machine / VPS
1. `git clone <repo>` (or copy the folder).
2. `cp .env.example .env` and paste your saved keys.
3. `python3 -m pip install --user openai pytest`
4. `bash scripts/healthcheck.sh` → expect "Health check passed".
5. `python main.py` boots; `python -m pytest` should pass.
6. Restart the Telegram service: `sudo systemctl restart sportverse` (if deployed).

## If a secret leaks
1. Rotate it immediately at the provider.
2. Update `.env`.
3. Run the Security Agent: `python -c "from agents.security_agent import SecurityAgent; print(SecurityAgent().report())"`.
4. If it was committed, purge from git history and force-push a clean history.

## If the bot/app won't start
- Check `logs/sportverse.log` and `journalctl -u sportverse -f`.
- Re-run `bash scripts/healthcheck.sh` to localize the failure.
- DeepSeek down or key missing → the model router falls back to mock automatically (no crash).
