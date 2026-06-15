#!/usr/bin/env bash
# Sportsverse — health check. Verifies the app imports, boots, and tests pass.
set -euo pipefail

APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$APP_DIR"
PY="${PYTHON:-python3}"

echo "== Health check =="

echo "[1/3] Import core packages..."
"$PY" - <<'PYEOF'
import importlib
for m in ("core.config", "agents.hermes", "agents.jarvis", "orchestration.langgraph_app",
          "providers.model_router", "approval.approval_queue", "dashboard.render"):
    importlib.import_module(m)
print("imports OK")
PYEOF

echo "[2/3] Boot the Phase 1-3 org (no loops, nothing sent)..."
"$PY" main.py >/dev/null && echo "boot OK"

echo "[3/3] Run tests if pytest is available..."
if "$PY" -c "import pytest" 2>/dev/null; then
  "$PY" -m pytest -q
else
  echo "pytest not installed; skipping (install with: $PY -m pip install --user pytest)"
fi

echo "== Health check passed =="
