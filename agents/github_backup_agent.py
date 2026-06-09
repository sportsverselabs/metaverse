"""GitHub backup agent — safe code backup. Protects secrets; never force-pushes; never commits .env.

It checks that secrets are gitignored, reports whether a repo/remote exists, and produces the
exact push commands once the owner supplies a repo URL. The actual git commands run via
``scripts/backup_github.sh``.
"""

from __future__ import annotations

from core import paths
from core.logging_setup import get_logger

# Files/patterns that must NEVER be committed.
MUST_IGNORE = [".env", "*.key", "*.pem"]


class GitHubBackupAgent:
    name = "github_backup_agent"

    def __init__(self, logger=None) -> None:
        self.log = logger or get_logger("agent.github_backup")

    def is_git_repo(self) -> bool:
        return (paths.PROJECT_ROOT / ".git").exists()

    def gitignore_protects_secrets(self) -> tuple[bool, list]:
        gi = paths.PROJECT_ROOT / ".gitignore"
        if not gi.exists():
            return False, MUST_IGNORE
        lines = {line.strip() for line in gi.read_text(encoding="utf-8").splitlines()}
        missing = [pat for pat in MUST_IGNORE if pat not in lines]
        return (not missing), missing

    def safety_check(self) -> dict:
        ok, missing = self.gitignore_protects_secrets()
        env_present = (paths.ENV_FILE).exists()
        return {
            "git_repo": self.is_git_repo(),
            "gitignore_protects_secrets": ok,
            "missing_ignores": missing,
            "env_exists_locally": env_present,
            "safe_to_commit": ok,  # if secrets are ignored, committing is safe
        }

    def backup_commands(self, repo_url: str = "<your-repo-url>") -> list:
        return [
            "git add -A",
            'git commit -m "Backup: Sportverse Labs system"',
            f"git remote add origin {repo_url}   # first time only",
            "git branch -M main",
            "git push -u origin main",
        ]

    def report(self) -> str:
        s = self.safety_check()
        lines = ["GitHub backup status:",
                 f"  git repo present: {s['git_repo']}",
                 f"  secrets protected by .gitignore: {s['gitignore_protects_secrets']}"]
        if s["missing_ignores"]:
            lines.append(f"  WARNING add to .gitignore: {s['missing_ignores']}")
        lines.append("  To back up: run scripts/backup_github.sh (or the commands in backup_commands()).")
        lines.append("  I need your GitHub repository URL (and a token if the repo is private).")
        return "\n".join(lines)
