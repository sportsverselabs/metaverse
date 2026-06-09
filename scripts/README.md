# scripts/

Helper scripts (start/stop the system, backups, setup, maintenance).
**Empty for now** — scripts depend on the chosen tech stack.

Guidelines:
- Keep scripts portable: relative paths, no hard-coded machine paths.
- No secrets in scripts — read from `.env`.
- Cross-platform where reasonable (the owner is on Windows now but may deploy to Linux VPS).
  Consider providing both a `.ps1` (Windows) and a `.sh` (Linux) when it matters.

Planned future scripts (examples):
- `start` / `stop` the system
- `backup` the project folder
- `setup` / install dependencies

> Created in Phase 1+ once the runtime is decided.
