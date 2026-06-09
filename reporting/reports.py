"""Daily and weekly report builders.

Deterministic, offline text reports assembled from the existing stores (journal, review queue,
approval queue, scheduler, cost ledger, analytics, security). No secrets included.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta

from agents.analytics_agent import AnalyticsAgent
from agents.dashboard_agent import DashboardAgent
from agents.security_agent import SecurityAgent, SEVERITY_OK
from orchestration.journal import AgentJournal


def _today_rows(rows: list) -> list:
    today = date.today().isoformat()
    return [r for r in rows if str(r.get("ts", "")).startswith(today)]


def _week_rows(rows: list) -> list:
    cutoff = (datetime.now() - timedelta(days=7)).isoformat()
    return [r for r in rows if str(r.get("ts", "")) >= cutoff]


def build_daily_report(*, dashboard=None, journal=None, analytics=None, security=None) -> str:
    dash = (dashboard or DashboardAgent()).assemble_data()
    journal = journal or AgentJournal()
    rows = journal.read()
    today = _today_rows(rows)
    sec = (security or SecurityAgent()).scan()
    sec_issues = [f for f in sec if f.severity != SEVERITY_OK]

    pend = dash["pending_approvals"]
    lines = [
        f"DAILY REPORT — SportVerse Labs — {date.today().isoformat()}",
        f"System: {dash['system_status']}",
        f"Tasks run today: {len(today)}",
        f"Pending approvals: {len(pend['content'])} content, {len(pend['actions'])} action(s)",
        "Published today: 0 (publishing is owner-gated; nothing posts automatically)",
        f"Cost this month: ${dash['cost']['month_total_usd']:.4f}",
        f"Security: {'OK' if not sec_issues else str(len(sec_issues)) + ' issue(s) — see /security'}",
        "Owner action items:",
    ]
    lines += [f"  - {t}" for t in dash["owner_todo"]]
    return "\n".join(lines)


def build_weekly_report(*, dashboard=None, journal=None, analytics=None) -> str:
    dash = (dashboard or DashboardAgent()).assemble_data()
    journal = journal or AgentJournal()
    week = _week_rows(journal.read())
    perf = (analytics or AnalyticsAgent()).summarize()

    by_route = {}
    for r in week:
        by_route[r.get("selected_route", "?")] = by_route.get(r.get("selected_route", "?"), 0) + 1

    lines = [
        f"WEEKLY REPORT — SportVerse Labs — week ending {date.today().isoformat()}",
        f"Tasks this week: {len(week)}",
        f"By agent: {by_route or '(none)'}",
        f"Best content: {perf.get('best')}",
        f"Worst content: {perf.get('worst')}",
        "Lessons learned:",
    ]
    lines += [f"  - {l}" for l in perf.get("lessons", [])]
    lines += [
        f"Cost this month so far: ${dash['cost']['month_total_usd']:.4f}",
        "Recommended next steps:",
        "  - Approve/schedule the strongest drafts in the review queue.",
        "  - Keep DeepSeek as default; enable Nemotron only for hard reasoning.",
        "  - When ready, begin Phase 5 publishing for ONE platform (owner-gated).",
    ]
    return "\n".join(lines)
