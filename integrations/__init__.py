"""Sportsverse OS — integrations package.

Connectors to external services. Phase 1 ships SKELETONS that never actually send:
they default to ``dry_run=True`` and log what they *would* do. This guarantees no
accidental outbound messages while the system is being built.

Safety rules baked in:
- No external publishing without explicit human approval.
- DM/comment replies must use an approved template id (free-text replies are blocked).
"""

from integrations.telegram_interface import TelegramInterface  # noqa: F401
from integrations.email_report import EmailReporter  # noqa: F401

__all__ = ["TelegramInterface", "EmailReporter"]
