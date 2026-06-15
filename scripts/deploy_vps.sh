#!/usr/bin/env bash
# Sportsverse — guided VPS deployment (run this ON the Hostinger VPS).
# It is interactive and asks before doing anything irreversible. It never echoes secrets.
set -euo pipefail

APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SERVICE_NAME="sportverse"
PY="${PYTHON:-python3}"

echo "== Sportsverse VPS deploy =="
echo "App dir: $APP_DIR"

confirm() { read -r -p "$1 [y/N] " a; [ "$a" = "y" ] || [ "$a" = "Y" ]; }

# 1) Prerequisites
command -v "$PY" >/dev/null || { echo "ERROR: python3 not found. Install it first."; exit 1; }
command -v git >/dev/null || echo "NOTE: git not found (needed for backups)."

# 2) Dependencies (DeepSeek uses the openai SDK). Handles PEP 668 (externally-managed) systems.
if confirm "Install Python dependency 'openai' (for DeepSeek live mode)?"; then
  "$PY" -m pip install --user openai 2>/dev/null \
    || "$PY" -m pip install --break-system-packages openai \
    || { echo "pip install failed — try: apt install -y python3-pip"; }
fi

# 3) .env
if [ ! -f "$APP_DIR/.env" ]; then
  echo "No .env found. Copying .env.example -> .env (you must paste your keys)."
  cp "$APP_DIR/.env.example" "$APP_DIR/.env"
  echo "Edit $APP_DIR/.env now and paste DEEPSEEK_API_KEY, TELEGRAM_BOT_TOKEN, etc."
  echo "NEVER commit .env (it is gitignored)."
fi

# 4) Health check
echo "Running health check..."
bash "$APP_DIR/scripts/healthcheck.sh" || { echo "Health check failed. Fix before continuing."; exit 1; }

# 5) systemd service (keeps the Telegram bot running)
if confirm "Install a systemd service to run the Jarvis Telegram bot continuously?"; then
  UNIT="/etc/systemd/system/${SERVICE_NAME}.service"
  echo "Writing $UNIT (requires sudo)..."
  sudo tee "$UNIT" >/dev/null <<EOF
[Unit]
Description=Sportsverse - Jarvis Telegram bot
After=network-online.target

[Service]
Type=simple
WorkingDirectory=$APP_DIR
ExecStart=$PY $APP_DIR/scripts/run_telegram.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
  sudo systemctl daemon-reload
  sudo systemctl enable --now "$SERVICE_NAME"
  echo "Service '$SERVICE_NAME' enabled. Check: sudo systemctl status $SERVICE_NAME"
fi

# 6) Dashboard (optional, behind a reverse proxy + SSL — see docs/DEPLOYMENT_GUIDE.md)
echo "To run the dashboard:  $PY -m dashboard --host 127.0.0.1 --port 8787"
echo "Then put nginx + certbot in front for https on sportsversenews.com."

echo "== Deploy steps complete. Send /status to your Telegram bot to confirm control. =="
