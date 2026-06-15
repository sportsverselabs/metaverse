"""Documentation agent — keeps the project docs discoverable and current.

The docs themselves live as real Markdown files under ``docs/``. This agent provides the
canonical list and a machine-readable directory of every agent + what it does.
"""

from __future__ import annotations

from core import paths
from core.logging_setup import get_logger

DOC_FILES = {
    "architecture": "docs/ARCHITECTURE.md",
    "user_manual": "docs/USER_MANUAL.md",
    "deployment_guide": "docs/DEPLOYMENT_GUIDE.md",
    "agent_directory": "docs/AGENT_DIRECTORY.md",
    "account_inventory": "docs/ACCOUNT_INVENTORY.md",
    "recovery_guide": "docs/RECOVERY_GUIDE.md",
}

AGENT_DIRECTORY = {
    "hermes": "Executive Officer — routes work, tracks cost/risk, requires approval for production actions.",
    "jarvis": "Command interface — Telegram/CLI/voice; turns requests into structured tasks for Hermes.",
    "research_agent": "Finds topics/trends/angles; prepares research briefs (DeepSeek).",
    "content_agent": "Writes articles/scripts/captions/titles/hashtags per platform (DeepSeek).",
    "video_agent": "Video concepts, scripts, metadata; CapCut editing note; draft only.",
    "social_publishing_agent": "Prepares posts for YT/IG/TikTok/website; never posts without approval + Phase 5.",
    "approval_agent": "Unified approve/reject/request-edit/upload/confirm surface; nothing publishes.",
    "analytics_agent": "Tracks performance; learns owner preferences from approvals/edits.",
    "security_agent": "Watches logs/secrets/backups/uptime; alerts to Telegram.",
    "deployment_agent": "VPS deploy checklist + asks for the exact missing credential.",
    "github_backup_agent": "Safe code backup; protects secrets; produces push commands.",
    "dns_website_agent": "DNS records to connect sportsversusnews.com; verifies resolution/SSL.",
    "dashboard_agent": "Assembles the owner dashboard data (read-only).",
    "documentation_agent": "Maintains architecture/user-manual/deploy/recovery/account docs.",
    "openclaw_skill_agent": "Controlled skill adapter; allowlist only; never the orchestrator.",
    "nemotron_reasoning_agent": "Optional high-reasoning specialist; off by default; falls back to DeepSeek.",
    "compliance": "Reviews content across policy/copyright/fair-use/FTC/brand-safety/platform; never auto-approves.",
    "sentinel": "Integrity/security/drift monitor for skills.",
    "archivist": "Institutional memory + handoff keeper.",
}


class DocumentationAgent:
    name = "documentation_agent"

    def __init__(self, logger=None) -> None:
        self.log = logger or get_logger("agent.documentation")

    def docs(self) -> dict:
        return {k: (paths.PROJECT_ROOT / v) for k, v in DOC_FILES.items()}

    def missing_docs(self) -> list:
        return [k for k, p in self.docs().items() if not p.exists()]

    def agent_directory(self) -> dict:
        return dict(AGENT_DIRECTORY)
