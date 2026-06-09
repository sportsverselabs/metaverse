# VPS Setup & Deployment Guide (Shell)

> How to move Sportsverse OS to a VPS and run it.
> SHELL ONLY — final commands depend on the chosen tech stack (not decided yet).
> Do not deploy until Phase 5. Last updated: 2026-06-08

---

## ⚠️ Read first

- The runtime (language/framework) is **not chosen yet**, so the exact install/run
  commands below are placeholders marked `[STACK-DEPENDENT]`. Fill them in once the
  stack is decided (`OWNER_ACTION_REQUIRED.md`, Action 2).
- The owner may use a **separate/new VPS** for this project. **Do not assume** any
  existing VPS is the final home.

---

## 1. What you need

- A Linux VPS (e.g. Ubuntu 22.04+), 1 vCPU / 1–2 GB RAM is a fine starting point.
- SSH access (host, username, and a key or password).
- The `sportsverse-os/` folder (copied or pulled from git).
- The runtime software for the chosen stack `[STACK-DEPENDENT]`
  (e.g. Python 3.x, or Node.js — TBD).

## 2. Required software (template)

```bash
# Update the box
sudo apt update && sudo apt upgrade -y

# Common tools
sudo apt install -y git curl

# Runtime — fill in once stack is chosen:
# [STACK-DEPENDENT]  e.g. python3 python3-venv  OR  node + npm
```

## 3. Move the project to the VPS

Pick ONE:

**A) Copy the folder directly (no git needed)**
```bash
# from your local machine:
scp -r "sportsverse-os" <user>@<vps-host>:~/sportsverse-os
```

**B) Via git (if you use a repo)**
```bash
git clone <your-repo-url> sportsverse-os
```

## 4. Configure secrets

```bash
cd sportsverse-os
cp .env.example .env
nano .env        # fill in real values — NEVER commit this file
```

## 5. Install dependencies (template)

```bash
cd sportsverse-os
# [STACK-DEPENDENT] e.g.:
#   python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
#   npm install
```

## 6. Start the system (template)

```bash
# [STACK-DEPENDENT] e.g.:
#   python3 scripts/start.py
#   npm run start
```

To keep it running after you log out, use a process manager (choose at deploy time):
- `systemd` service (recommended, built-in, free), **or**
- `tmux`/`screen` (simplest), **or**
- `pm2` (if Node).

`[STACK-DEPENDENT]` — add the exact service file / command here when known.

## 7. Stop the system (template)

```bash
# [STACK-DEPENDENT] e.g.:
#   sudo systemctl stop sportsverse
#   pm2 stop sportsverse
#   Ctrl-C inside the tmux/screen session
```

## 8. Back it up

The whole project is one folder, so backups are simple:

```bash
# On the VPS — create a timestamped archive (excludes secrets & logs is safer):
tar --exclude='.env' --exclude='logs/*' -czf sportsverse-backup-$(date +%F).tar.gz sportsverse-os

# Copy it off the VPS to your local machine:
scp <user>@<vps-host>:~/sportsverse-backup-*.tar.gz .
```

Keep at least one backup **off** the VPS (local machine or external drive).
Back up `.env` separately and securely (it holds secrets) — do not put it in the same
public/shared place as the code.

## 9. Checklist before going live

- [ ] Stack chosen and sections 2/5/6/7 filled in
- [ ] `.env` created on the VPS with real values
- [ ] Process manager configured (survives reboot/logout)
- [ ] Backup tested (can restore from the archive)
- [ ] Logs writing to `logs/` and rotating
- [ ] No secrets committed anywhere
