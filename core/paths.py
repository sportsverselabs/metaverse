"""Canonical project paths.

Every path is derived **relative to this file**, so the whole project stays
portable: copy ``sportsverse-os/`` anywhere (external drive, VPS, another machine)
and these paths still resolve. Never hard-code an absolute machine path elsewhere —
import from here instead.

Layout assumption: every Python source file lives exactly one directory below the
project root (e.g. ``core/``, ``agents/``), so ``parents[1]`` from any of them is root.
"""

from __future__ import annotations

from pathlib import Path

# ``core/paths.py`` -> parents[0] = core/ , parents[1] = project root
PROJECT_ROOT: Path = Path(__file__).resolve().parents[1]

# Top-level folders (see README.md for the full map)
CONFIG_DIR: Path = PROJECT_ROOT / "config"
LOGS_DIR: Path = PROJECT_ROOT / "logs"
MEMORY_DIR: Path = PROJECT_ROOT / "memory"
MEMORY_STORE: Path = MEMORY_DIR / "store"
REPORTS_DIR: Path = PROJECT_ROOT / "reports"
HANDOFF_DIR: Path = REPORTS_DIR / "handoff"
REVIEW_DIR: Path = REPORTS_DIR / "review"
SCHEDULE_DIR: Path = REPORTS_DIR / "schedule"
APPROVALS_DIR: Path = REPORTS_DIR / "approvals"
KNOWLEDGE_DIR: Path = PROJECT_ROOT / "knowledge_library"

# Well-known files
ENV_FILE: Path = PROJECT_ROOT / ".env"
ENV_EXAMPLE_FILE: Path = PROJECT_ROOT / ".env.example"
SETTINGS_FILE: Path = CONFIG_DIR / "settings.json"
SETTINGS_EXAMPLE_FILE: Path = CONFIG_DIR / "settings.example.json"
MODEL_BUDGET_FILE: Path = CONFIG_DIR / "model_budget.json"
OPENCLAW_ALLOWLIST_FILE: Path = CONFIG_DIR / "openclaw_allowlist.json"
LOG_FILE: Path = LOGS_DIR / "sportsverse.log"
AGENT_JOURNAL: Path = LOGS_DIR / "agent_journal.jsonl"
LATEST_HANDOFF: Path = HANDOFF_DIR / "latest_handoff.md"


def ensure_runtime_dirs() -> None:
    """Create the directories runtime code writes to, if missing. Safe to call repeatedly."""
    for d in (LOGS_DIR, MEMORY_STORE, HANDOFF_DIR, REVIEW_DIR, SCHEDULE_DIR, APPROVALS_DIR):
        d.mkdir(parents=True, exist_ok=True)
