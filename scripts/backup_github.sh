#!/usr/bin/env bash
# SportVerse Labs — safe GitHub backup. Refuses to run if secrets would be committed.
set -euo pipefail

APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$APP_DIR"

echo "== SportVerse Labs GitHub backup =="

# 1) Safety: .gitignore must protect .env
if ! grep -qxF ".env" .gitignore; then
  echo "ABORT: .env is not in .gitignore. Refusing to risk committing secrets."
  exit 1
fi

# 2) Init repo if needed
if [ ! -d .git ]; then
  echo "Initializing git repository..."
  git init
  git branch -M main
fi

# 3) Hard stop if .env is somehow tracked
if git ls-files --error-unmatch .env >/dev/null 2>&1; then
  echo "ABORT: .env is tracked by git. Run: git rm --cached .env   then retry."
  exit 1
fi

# 4) Stage + commit
git add -A
if git diff --cached --quiet; then
  echo "Nothing to commit."
else
  git commit -m "Backup: SportVerse Labs system ($(date -u +%Y-%m-%dT%H:%M:%SZ))"
fi

# 5) Remote + push
REMOTE_URL="${1:-}"
if [ -z "$REMOTE_URL" ]; then
  if git remote get-url origin >/dev/null 2>&1; then
    echo "Pushing to existing origin..."
    git push -u origin main
  else
    echo "No remote set. Re-run with your repo URL:"
    echo "  bash scripts/backup_github.sh https://github.com/<you>/<repo>.git"
    echo "(For a private repo, configure a token/credential helper first.)"
  fi
else
  git remote add origin "$REMOTE_URL" 2>/dev/null || git remote set-url origin "$REMOTE_URL"
  git push -u origin main
fi

echo "== Backup complete (secrets excluded). =="
