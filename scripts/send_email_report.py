"""Email a Sportsverse report to the owner.

    python scripts/send_email_report.py            # daily report
    python scripts/send_email_report.py --weekly    # weekly report
    python scripts/send_email_report.py --test      # short connectivity test email

Reads EMAIL_ADDRESS / EMAIL_APP_PASSWORD (and optional SMTP_HOST/PORT) from .env.
Sends to the owner address by default. Never prints or logs the password.
Safe to run from cron. This is an internal owner report, not public posting.
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.config import load_config
from core.console import enable_utf8_console
from integrations.email_report import EmailReporter
from reporting.reports import build_daily_report, build_weekly_report


def main() -> int:
    enable_utf8_console()
    config = load_config()
    reporter = EmailReporter(config)

    if not reporter.configured:
        print("Email not configured. Set EMAIL_ADDRESS and EMAIL_APP_PASSWORD in .env.")
        return 1

    if "--test" in sys.argv:
        subject = "Sportsverse — email test"
        body = ("This is a Sportsverse connectivity test.\n"
                f"Sent {datetime.now().isoformat(timespec='seconds')}.\n"
                "If you can read this, owner email reports are working.")
    elif "--weekly" in sys.argv:
        subject = "Sportsverse — Weekly Report"
        body = build_weekly_report()
    else:
        subject = "Sportsverse — Daily Report"
        body = build_daily_report()

    result = reporter.send_report(subject, body)
    if result.sent:
        print(f"OK: sent '{subject}' to {result.data.get('to')}")
        return 0
    print(f"NOT SENT: {result.detail}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
