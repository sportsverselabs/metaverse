"""Telegram interface (skeleton).

A thin wrapper around the Telegram Bot API. Phase 1 status: SKELETON — it does NOT
call the network. It validates inputs, enforces safety policy, and logs intent.

Safety policy (owner rules):
- DM / comment replies may ONLY be sent from an approved template (``template_id``).
  Free-text replies are blocked.
- ``dry_run`` defaults to True. Real sending is enabled only when (a) a bot token is
  configured AND (b) ``dry_run`` is explicitly turned off in a later phase.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from core.logging_setup import get_logger

# Approved reply templates. Real templates are owner-authored and added in a later phase.
APPROVED_TEMPLATES: dict[str, str] = {
    # "welcome": "Thanks for reaching out! ...",
}


@dataclass
class SendResult:
    sent: bool
    detail: str
    dry_run: bool = True
    data: dict = field(default_factory=dict)


class TelegramInterface:
    def __init__(self, config=None, logger=None, dry_run: bool = True) -> None:
        self.config = config
        self.log = logger or get_logger("integration.telegram")
        self.dry_run = dry_run
        self._token = config.secret("TELEGRAM_BOT_TOKEN") if config else None

    @property
    def configured(self) -> bool:
        return bool(self._token)

    def send_template_reply(self, chat_id: str, template_id: str, variables: Optional[dict] = None) -> SendResult:
        """Send a reply built from an APPROVED template only.

        SKELETON: never hits the network. Blocks unknown templates. Logs intent.
        """
        if template_id not in APPROVED_TEMPLATES:
            self.log.warning("Blocked reply: template '%s' is not approved.", template_id)
            return SendResult(False, f"template '{template_id}' is not approved", self.dry_run)

        if self.dry_run or not self.configured:
            reason = "dry_run" if self.dry_run else "no bot token configured"
            self.log.info("[dry] Would send template '%s' to chat %s (%s)", template_id, chat_id, reason)
            return SendResult(False, f"not sent ({reason})", True, {"template_id": template_id})

        # TODO(later-phase): real send via Telegram Bot API (requests/httpx).
        return SendResult(False, "real send not implemented (Phase 1 skeleton)", False)

    def send_free_text(self, chat_id: str, text: str) -> SendResult:
        """Free-text replies are NOT allowed by policy. Always blocked."""
        self.log.warning("Blocked free-text Telegram reply (policy: templates only).")
        return SendResult(False, "free-text replies are blocked by policy; use an approved template", self.dry_run)

    def poll_updates(self) -> list:
        """SKELETON: fetch incoming updates. Returns [] until implemented."""
        self.log.debug("poll_updates: skeleton (returns no updates)")
        return []
