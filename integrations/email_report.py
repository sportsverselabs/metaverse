"""Email report sender.

Sends internal status/intelligence reports to the OWNER (not public posting), e.g. a
daily affiliate-intelligence digest, over SMTP (Gmail by default).

Notes:
- Internal owner reports are not "public posting", so they don't need the publishing
  approval gate — but they ``dry_run`` automatically until SMTP creds are configured.
- Credentials come from ``.env`` (EMAIL_ADDRESS / EMAIL_APP_PASSWORD / SMTP_HOST / SMTP_PORT).
  SMTP_HOST defaults to smtp.gmail.com. Never hard-code creds and never log them.
"""

from __future__ import annotations

import smtplib
from dataclasses import dataclass, field
from email.mime.text import MIMEText  # stdlib
from typing import Optional

from core.logging_setup import get_logger

DEFAULT_SMTP_HOST = "smtp.gmail.com"
DEFAULT_SMTP_PORT = 587


@dataclass
class EmailResult:
    sent: bool
    detail: str
    dry_run: bool = True
    data: dict = field(default_factory=dict)


class EmailReporter:
    def __init__(self, config=None, logger=None, dry_run: bool = False) -> None:
        self.config = config
        self.log = logger or get_logger("integration.email")
        self.dry_run = dry_run
        self._address = config.secret("EMAIL_ADDRESS") if config else None
        self._password = config.secret("EMAIL_APP_PASSWORD") if config else None
        self._smtp_host = (config.get("SMTP_HOST") if config else None) or DEFAULT_SMTP_HOST
        self._smtp_port = int(config.get("SMTP_PORT", DEFAULT_SMTP_PORT)) if config else DEFAULT_SMTP_PORT

    @property
    def configured(self) -> bool:
        return bool(self._address and self._password and self._smtp_host)

    def build_message(self, subject: str, body: str, to: str) -> MIMEText:
        """Build a plain-text email message object (no network)."""
        msg = MIMEText(body, _charset="utf-8")
        msg["Subject"] = subject
        msg["From"] = self._address or "sportsverse-os@localhost"
        msg["To"] = to
        return msg

    def send_report(self, subject: str, body: str, to: Optional[str] = None) -> EmailResult:
        """Send an internal report to the owner.

        SKELETON: builds the message and logs intent; does not connect to SMTP.
        """
        recipient = to or self._address  # default: email the owner's own address
        if not recipient:
            return EmailResult(False, "no recipient and no EMAIL_ADDRESS configured", self.dry_run)

        msg = self.build_message(subject, body, recipient)  # validates inputs

        if self.dry_run or not self.configured:
            reason = "dry_run" if self.dry_run else "SMTP not fully configured"
            self.log.info("[dry] Would email report '%s' to %s (%s)", subject, recipient, reason)
            return EmailResult(False, f"not sent ({reason})", True, {"subject": subject, "to": recipient})

        try:
            with smtplib.SMTP(self._smtp_host, self._smtp_port, timeout=30) as s:
                s.ehlo()
                s.starttls()
                s.login(self._address, self._password)  # password never logged
                s.send_message(msg)
        except Exception as exc:  # surface the failure type without leaking creds
            self.log.error("Email send failed to %s: %s", recipient, type(exc).__name__)
            return EmailResult(False, f"send failed: {type(exc).__name__}: {exc}", False,
                               {"subject": subject, "to": recipient})

        self.log.info("Emailed report '%s' to %s", subject, recipient)
        return EmailResult(True, "sent", False, {"subject": subject, "to": recipient})
