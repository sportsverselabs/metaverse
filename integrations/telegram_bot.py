"""Jarvis Telegram bot — owner control over the system from Telegram.

Implements the command set. Built on the stdlib (urllib) so there's no extra dependency. It is
token-gated and dry-run by default: with no ``TELEGRAM_BOT_TOKEN`` it never hits the network and
``send()`` just returns the text. ``dispatch(text)`` is a pure function (testable offline).

Safety: only the configured ``TELEGRAM_CHAT_ID`` is authorized (if set). Approve/reject/edit map
to the review/approval surfaces — they NEVER publish; nothing posts to any platform from here.
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from typing import Optional

from core.config import load_config
from core.logging_setup import get_logger

HELP = (
    "Jarvis commands:\n"
    "/status — system status\n"
    "/today — daily report\n"
    "/weekly — weekly report\n"
    "/approvals — pending approvals\n"
    "/approve <id> — approve a draft\n"
    "/reject <id> <reason> — reject a draft\n"
    "/edit <id> <notes> — request edits\n"
    "/drafts — list draft content\n"
    "/publish_queue — scheduled slots\n"
    "/cost — cost usage\n"
    "/security — security scan\n"
    "/backup — backup status\n"
    "/deploy_status — deployment checklist\n"
    "/help — this help"
)


class JarvisTelegramBot:
    def __init__(self, config=None, logger=None) -> None:
        self.config = config or load_config()
        self.log = logger or get_logger("telegram")
        self._token = self.config.secret("TELEGRAM_BOT_TOKEN")
        self._chat_id = self.config.get("TELEGRAM_CHAT_ID")

    @property
    def configured(self) -> bool:
        return bool(self._token)

    # ------------------------------------------------------------------ #
    def authorized(self, chat_id) -> bool:
        if not self._chat_id:
            return True  # no restriction configured yet
        return str(chat_id) == str(self._chat_id)

    def dispatch(self, text: str, *, from_chat_id=None) -> str:
        """Map a command string to a reply. Pure + offline (no network)."""
        if from_chat_id is not None and not self.authorized(from_chat_id):
            return "Unauthorized."
        text = (text or "").strip()
        if not text.startswith("/"):
            return "Send a command. Try /help"
        parts = text.split()
        cmd, args = parts[0].lower().lstrip("/"), parts[1:]
        try:
            return self._handle(cmd, args)
        except Exception as exc:  # never crash the bot loop
            self.log.error("command '%s' failed: %s", cmd, exc)
            return f"Sorry, '{cmd}' failed: {exc}"

    def _handle(self, cmd: str, args: list) -> str:
        if cmd in ("help", "start"):
            return HELP
        if cmd == "status":
            from agents.dashboard_agent import DashboardAgent
            d = DashboardAgent().assemble_data()
            p = d["pending_approvals"]
            return (f"Status: {d['system_status']}\nCost (month): ${d['cost']['month_total_usd']:.4f}\n"
                    f"Pending: {len(p['content'])} content, {len(p['actions'])} action(s)\nNothing auto-publishes.")
        if cmd == "today":
            from reporting.reports import build_daily_report
            return build_daily_report()
        if cmd == "weekly":
            from reporting.reports import build_weekly_report
            return build_weekly_report()
        if cmd in ("approvals", "drafts"):
            from agents.approval_agent import ApprovalAgent
            pend = ApprovalAgent().pending()
            lines = ["Pending content:"]
            lines += [f"  {c['id']}  {c['skill']}  risk {c['risk']}" for c in pend["content"]] or ["  (none)"]
            lines.append("Pending actions:")
            lines += [f"  {a['id']}  {a['action']}" for a in pend["actions"]] or ["  (none)"]
            return "\n".join(lines)
        if cmd == "approve":
            if not args:
                return "Usage: /approve <id>"
            from agents.approval_agent import ApprovalAgent
            item = ApprovalAgent().approve(args[0])
            return f"Approved {item.id} -> {item.status} (draft approved; NOT published)."
        if cmd == "reject":
            if len(args) < 1:
                return "Usage: /reject <id> <reason>"
            from agents.approval_agent import ApprovalAgent
            reason = " ".join(args[1:]) or "rejected via Telegram"
            item = ApprovalAgent().reject(args[0], reason)
            return f"Rejected {item.id}. Reason: {reason}"
        if cmd == "edit":
            if len(args) < 2:
                return "Usage: /edit <id> <notes>"
            from agents.approval_agent import ApprovalAgent
            out = ApprovalAgent().request_edit(args[0], " ".join(args[1:]))
            return f"Edit requested for {out['item'].id}. A revised draft will be prepared."
        if cmd == "publish_queue":
            from scheduler.store import SchedulerStore
            slots = SchedulerStore().list()
            if not slots:
                return "No scheduled slots. Nothing is queued to post (and nothing posts automatically)."
            return "Scheduled slots:\n" + "\n".join(f"  {s.id} [{s.status}] {s.scheduled_for} <- {s.review_id}" for s in slots)
        if cmd == "cost":
            from providers.model_router import CostTracker
            return f"Estimated spend this month: ${CostTracker().month_total():.4f} (DeepSeek default; over-budget tasks pause for approval)."
        if cmd == "security":
            from agents.security_agent import SecurityAgent
            return SecurityAgent().report()
        if cmd == "backup":
            from agents.github_backup_agent import GitHubBackupAgent
            return GitHubBackupAgent().report()
        if cmd == "deploy_status":
            from agents.deployment_agent import DeploymentAgent
            return DeploymentAgent().report()
        return f"Unknown command '/{cmd}'. Try /help"

    # ------------------------------------------------------------------ #
    def send(self, text: str, chat_id=None) -> dict:
        """Send a message. Dry-run (no network) if no token is configured."""
        chat = chat_id or self._chat_id
        if not self.configured or not chat:
            self.log.info("[dry] Telegram send (no token/chat): %s", text[:80])
            return {"sent": False, "reason": "telegram not configured (dry-run)"}
        try:
            url = f"https://api.telegram.org/bot{self._token}/sendMessage"
            data = urllib.parse.urlencode({"chat_id": chat, "text": text}).encode()
            with urllib.request.urlopen(urllib.request.Request(url, data=data), timeout=15) as resp:
                return {"sent": True, "status": resp.status}
        except Exception as exc:
            self.log.error("telegram send failed: %s", exc)
            return {"sent": False, "reason": str(exc)}

    def run_polling(self, interval: float = 2.0) -> None:  # pragma: no cover (needs live token)
        """Long-poll Telegram for commands and reply. Requires a token; Ctrl-C to stop."""
        if not self.configured:
            print("TELEGRAM_BOT_TOKEN not set. Add it to .env, then run again.")
            return
        import time
        offset = 0
        base = f"https://api.telegram.org/bot{self._token}"
        print("Jarvis Telegram bot running. Send /help. Ctrl-C to stop.")
        while True:
            try:
                url = f"{base}/getUpdates?timeout=20&offset={offset}"
                with urllib.request.urlopen(url, timeout=30) as resp:
                    updates = json.loads(resp.read()).get("result", [])
                for u in updates:
                    offset = u["update_id"] + 1
                    msg = u.get("message") or {}
                    text = msg.get("text", "")
                    chat = (msg.get("chat") or {}).get("id")
                    if text:
                        self.send(self.dispatch(text, from_chat_id=chat), chat_id=chat)
                time.sleep(interval)
            except KeyboardInterrupt:
                print("\nStopped.")
                return
            except Exception as exc:
                self.log.error("polling error: %s", exc)
                time.sleep(5)
