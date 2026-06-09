"""Reporting — daily and weekly owner reports (text, sent via Telegram or shown on the dashboard)."""

from reporting.reports import build_daily_report, build_weekly_report  # noqa: F401

__all__ = ["build_daily_report", "build_weekly_report"]
