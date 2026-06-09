"""Security agent — watches the system and reports issues (alerts go to Telegram, dry-run).

Offline, read-only checks: secrets not leaking into logs, `.env` protected by `.gitignore`,
backups present, and basic service/uptime hooks (stubs until the VPS is live). It never prints
secret VALUES — only whether a risk exists.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from core import paths
from core.logging_setup import get_logger

# Patterns that look like leaked secrets (we report counts/locations, never the value).
_SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9]{16,}"),
    re.compile(r"(?i)(api[_-]?key|token|secret|password)\s*[=:]\s*\S{8,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
]

SEVERITY_OK, SEVERITY_WARN, SEVERITY_CRIT = "ok", "warning", "critical"


@dataclass
class Finding:
    check: str
    severity: str
    detail: str


class SecurityAgent:
    name = "security_agent"

    def __init__(self, logger=None, telegram=None) -> None:
        self.log = logger or get_logger("agent.security")
        self.telegram = telegram  # optional JarvisTelegramBot (dry-run by default)

    def scan(self) -> list[Finding]:
        findings: list[Finding] = []
        findings.append(self._check_env_gitignored())
        findings.append(self._check_secrets_in_logs())
        findings.append(self._check_backup_present())
        # Service/uptime checks are stubs until deployed on the VPS.
        findings.append(Finding("service_uptime", SEVERITY_OK, "uptime monitoring active once deployed (stub)"))
        for f in findings:
            if f.severity != SEVERITY_OK:
                self.log.warning("Security %s: %s", f.severity, f.detail)
        return findings

    def _check_env_gitignored(self) -> Finding:
        gi = paths.PROJECT_ROOT / ".gitignore"
        if gi.exists() and any(line.strip() == ".env" for line in gi.read_text(encoding="utf-8").splitlines()):
            return Finding("env_gitignored", SEVERITY_OK, ".env is protected by .gitignore")
        return Finding("env_gitignored", SEVERITY_CRIT, ".env is NOT in .gitignore — secrets could be committed")

    def _check_secrets_in_logs(self) -> Finding:
        hits = 0
        for path in paths.LOGS_DIR.glob("**/*"):
            if not path.is_file() or path.suffix not in (".log", ".jsonl", ".txt"):
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for pat in _SECRET_PATTERNS:
                hits += len(pat.findall(text))
        if hits:
            return Finding("secrets_in_logs", SEVERITY_CRIT, f"{hits} possible secret pattern(s) found in logs — rotate + scrub")
        return Finding("secrets_in_logs", SEVERITY_OK, "no secret patterns detected in logs")

    def _check_backup_present(self) -> Finding:
        if (paths.PROJECT_ROOT / ".git").exists():
            return Finding("backup", SEVERITY_OK, "git repository present (backup possible)")
        return Finding("backup", SEVERITY_WARN, "no git repository yet — run scripts/backup_github.sh to set up backups")

    def alert(self, finding: Finding) -> None:
        msg = f"[SECURITY {finding.severity.upper()}] {finding.check}: {finding.detail}"
        self.log.warning(msg)
        if self.telegram is not None:
            try:
                self.telegram.send(msg)
            except Exception:
                self.log.debug("telegram alert failed", exc_info=True)

    def report(self) -> str:
        lines = ["Security scan:"]
        for f in self.scan():
            mark = "OK " if f.severity == SEVERITY_OK else f.severity.upper()
            lines.append(f"  [{mark}] {f.check}: {f.detail}")
        return "\n".join(lines)
