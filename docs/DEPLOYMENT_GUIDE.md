# Sportsverse — Deployment Guide (Hostinger VPS)

Goal: run the system continuously on your Hostinger VPS, controlled via Telegram, with the
dashboard and (later) website on sportsversusnews.com. **Nothing publishes without your approval.**

> The Deployment Agent will ask you for each missing item in plain English, one at a time.

## What you'll be asked for (have these ready)
1. Hostinger **VPS IP address**
2. **VPS username** (often `root` or a sudo user) + SSH login (key preferred)
3. **DeepSeek API key** (already set locally)
4. **Telegram bot token** (from @BotFather) and your **Telegram chat id**
5. **GitHub repo URL** (+ token if private) for backups
6. **Hostinger DNS** access to point the domain at the VPS

## Step-by-step
1. **Back up first:** `bash scripts/backup_github.sh https://github.com/<you>/<repo>.git`
   (Secrets are excluded by `.gitignore`; the script refuses to commit `.env`.)
2. **Get the code on the VPS:** `git clone <repo>` (or `scp -r` the folder).
3. **Install runtime:**
   ```
   sudo apt update && sudo apt install -y python3 python3-pip git
   python3 -m pip install --user openai pytest
   ```
4. **Secrets:** `cp .env.example .env` then edit `.env` and paste your keys. Never commit it.
5. **Health check:** `bash scripts/healthcheck.sh` (imports + boot + tests).
6. **Run continuously:** `bash scripts/deploy_vps.sh` installs a `systemd` service that runs the
   Jarvis Telegram bot and restarts on failure.
7. **Dashboard:** `python3 -m dashboard --host 127.0.0.1 --port 8787`.
8. **Reverse proxy + SSL (for the website/dashboard):** install nginx + certbot:
   ```
   sudo apt install -y nginx certbot python3-certbot-nginx
   # proxy_pass http://127.0.0.1:8787; for dashboard.sportsversusnews.com
   sudo certbot --nginx -d sportsversusnews.com -d www.sportsversusnews.com
   ```
9. **DNS:** in Hostinger, add A records (`@`, `www`, `dashboard`) → your VPS IP
   (the DNS agent prints exact records; `DnsWebsiteAgent.instructions(<ip>)`).
10. **Confirm:** send `/status` to the Telegram bot; open the dashboard; verify the site resolves.

## Operating
- Start/stop bot: `sudo systemctl start|stop sportverse`
- Logs: `journalctl -u sportverse -f` and `logs/sportverse.log`
- Backups: re-run `scripts/backup_github.sh` (or cron it).
- Updates: `git pull` on the VPS, then `sudo systemctl restart sportverse`.

## Stop / rollback
`sudo systemctl stop sportverse`. The project is one portable folder; restore from your GitHub
backup or a copy. See `docs/RECOVERY_GUIDE.md`.
