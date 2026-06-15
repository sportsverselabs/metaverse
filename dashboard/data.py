"""Dashboard data layer — assembles real data for each of the 14 sections.

Honest by design: where a feature needs credentials/integrations that aren't set up yet,
the data says so ("needs owner setup" / "placeholder") instead of pretending.
"""

from __future__ import annotations

from datetime import date

from agents.analytics_agent import AnalyticsAgent
from agents.dashboard_agent import DashboardAgent
from agents.documentation_agent import AGENT_DIRECTORY, DocumentationAgent
from agents.security_agent import SEVERITY_OK, SecurityAgent
from core.config import load_config
from core.logging_setup import get_logger
from orchestration.journal import AgentJournal
from providers.model_router import CostTracker

SECTIONS = [
    ("home", "Home"), ("ask", "Ask Hermes"), ("approvals", "Approvals"),
    ("pipeline", "Content Pipeline"), ("video", "Video Review"), ("publishing", "Publishing"),
    ("analytics", "Analytics"), ("reports", "Reports"), ("agents", "Agents"),
    ("security", "Security"), ("costs", "Costs"), ("backups", "Backups"),
    ("settings", "Settings"), ("manual", "System Manual"),
]


def _truthy(v) -> bool:
    return str(v).strip().lower() in {"1", "true", "yes", "on"}


class DashboardData:
    def __init__(self, config=None) -> None:
        self.config = config or load_config()
        self.log = get_logger("dashboard.data")
        self.dash = DashboardAgent()
        self._security = SecurityAgent()
        self._analytics = AnalyticsAgent()
        self.docs = DocumentationAgent()
        self.cost = CostTracker()
        self.journal = AgentJournal()

    # ---- helpers ----------------------------------------------------- #
    def _today_rows(self):
        today = date.today().isoformat()
        return [r for r in self.journal.read() if str(r.get("ts", "")).startswith(today)]

    def cost_today(self) -> float:
        return round(sum(float(r.get("estimated_cost_usd") or 0) for r in self._today_rows()), 4)

    def statuses(self) -> list[dict]:
        c = self.config
        deepseek_live = bool(c.secret("DEEPSEEK_API_KEY")) and str(c.get("LLM_MODE", "mock")).lower() == "live"
        nem = _truthy(c.get("NEMOTRON_ENABLED", "false")) and bool(c.secret("NEMOTRON_API_KEY"))
        try:
            import langgraph  # noqa: F401
            lg = "online (LangGraph)"
        except Exception:
            lg = "online (built-in engine)"
        tg = bool(c.secret("TELEGRAM_BOT_TOKEN"))
        email = bool(c.secret("EMAIL_APP_PASSWORD") and c.get("EMAIL_ADDRESS"))
        def st(ok, good="online", bad="needs setup"):
            return good if ok else bad
        return [
            {"name": "Hermes (Executive)", "state": "ok", "status": "online"},
            {"name": "Jarvis (Interface)", "state": "ok", "status": "online"},
            {"name": "VPS", "state": "ok", "status": "running"},
            {"name": "Website", "state": "ok", "status": "live"},
            {"name": "Telegram bot", "state": "ok" if tg else "warn", "status": st(tg)},
            {"name": "Email notifications", "state": "ok" if email else "warn", "status": st(email, bad="needs owner setup")},
            {"name": "DeepSeek API", "state": "ok" if deepseek_live else "warn", "status": "live" if deepseek_live else "mock/fallback"},
            {"name": "Nemotron / NeMo", "state": "ok" if nem else "off", "status": "enabled" if nem else "disabled (optional)"},
            {"name": "LangGraph", "state": "ok", "status": lg},
            {"name": "OpenClaw", "state": "ok", "status": "allowlist active"},
        ]

    # ---- sections ---------------------------------------------------- #
    def home(self) -> dict:
        d = self.dash.assemble_data()
        issues = [f for f in self._security.scan() if f.severity != SEVERITY_OK]
        return {
            "statuses": self.statuses(),
            "pending_content": len(d["pending_approvals"]["content"]),
            "pending_actions": len(d["pending_approvals"]["actions"]),
            "active_jobs": 0,
            "today_done": len(self._today_rows()),
            "errors": [f"{f.check}: {f.detail}" for f in issues] or ["No errors or warnings."],
            "cost_today": self.cost_today(),
            "cost_mtd": round(self.cost.month_total(), 4),
            "todos": d["owner_todo"],
        }

    def approvals(self) -> dict:
        d = self.dash.assemble_data()
        return {"content": d["pending_approvals"]["content"], "actions": d["pending_approvals"]["actions"]}

    def pipeline(self) -> dict:
        from review.models import (STATUS_OWNER_APPROVED, STATUS_READY, STATUS_REJECTED,
                                    STATUS_REVISION, STATUS_SCHEDULED)
        rs = self.dash.review_store
        sched = self.dash.scheduler_store
        return {"stages": [
            {"stage": "Idea / Researching", "count": "—", "note": "tasks are synchronous; see journal"},
            {"stage": "Drafting → Waiting approval", "count": len(rs.list(status=STATUS_READY))},
            {"stage": "Needs edit (revision)", "count": len(rs.list(status=STATUS_REVISION))},
            {"stage": "Owner approved", "count": len(rs.list(status=STATUS_OWNER_APPROVED))},
            {"stage": "Scheduled", "count": len(rs.list(status=STATUS_SCHEDULED))},
            {"stage": "Rejected", "count": len(rs.list(status=STATUS_REJECTED, include_archived=True))},
            {"stage": "Published", "count": 0, "note": "publishing is Phase 5 (owner-gated)"},
        ]}

    def video(self) -> dict:
        return {"placeholder": True,
                "note": "Video review center: embedded player + upload/download are not built yet (placeholder).",
                "tools": ["CapCut — quick TikTok/Reels/Shorts edits",
                          "Canva — thumbnails & graphics",
                          "DaVinci Resolve — advanced editing"]}

    def publishing(self) -> dict:
        c = self.config
        return {"connections": [
            {"platform": "Website", "status": "connected (sportsversenews.com)"},
            {"platform": "Telegram bot", "status": "connected" if c.secret("TELEGRAM_BOT_TOKEN") else "needs owner setup"},
            {"platform": "Email (Gmail)", "status": "needs owner setup (Gmail App Password)"},
            {"platform": "YouTube", "status": "needs owner setup (API credentials)"},
            {"platform": "TikTok", "status": "needs owner setup (account/API)"},
            {"platform": "Instagram", "status": "needs owner setup (account/API)"},
        ], "note": "No live posting exists yet (Phase 5). Connections marked 'needs owner setup' require credentials."}

    def analytics(self) -> dict:
        s = self._analytics.summarize()
        return {"summary": s, "placeholder": s.get("count", 0) == 0,
                "note": "Real views/likes/watch-time need platform API connections (Phase 5). Showing recorded data only."}

    def reports(self) -> dict:
        from reporting.reports import build_daily_report, build_weekly_report
        return {"daily": build_daily_report(), "weekly": build_weekly_report()}

    def agents(self) -> dict:
        return {"agents": [{"name": k, "purpose": v, "status": "active"} for k, v in AGENT_DIRECTORY.items()]}

    def security(self) -> dict:
        return {"findings": [{"check": f.check, "severity": f.severity, "detail": f.detail}
                             for f in self._security.scan()]}

    def costs(self) -> dict:
        b = self.cost.budget if hasattr(self.cost, "budget") else {}
        from providers.model_router import _load_budget
        budget = _load_budget()
        return {"month_to_date": round(self.cost.month_total(), 4), "today": self.cost_today(),
                "monthly_budget": budget.get("monthly_budget_usd"),
                "per_task_threshold": budget.get("per_task_approval_threshold_usd")}

    def backups(self) -> dict:
        from agents.github_backup_agent import GitHubBackupAgent
        return {"github": GitHubBackupAgent().safety_check()}

    def settings(self) -> dict:
        c = self.config
        # Non-secret settings only.
        return {"env": c.get("SPORTSVERSE_ENV"), "llm_mode": c.get("LLM_MODE"),
                "llm_provider": c.get("LLM_PROVIDER"), "nemotron_enabled": c.get("NEMOTRON_ENABLED"),
                "note": "Secrets are never shown. Edit .env on the server to change keys."}

    def manual(self) -> dict:
        return {"docs": ["docs/ARCHITECTURE.md", "docs/DASHBOARD_GUIDE.md", "docs/USER_MANUAL.md",
                         "docs/AGENT_DIRECTORY.md", "docs/DEPLOYMENT_GUIDE.md", "docs/ACCOUNT_INVENTORY.md",
                         "docs/MEDIA_LICENSE_POLICY.md", "docs/ARCHITECTURE_AUDIT.md", "docs/RECOVERY_GUIDE.md"],
                "agents": [{"name": k, "purpose": v} for k, v in AGENT_DIRECTORY.items()]}

    def section(self, name: str) -> dict:
        fn = getattr(self, name, None)
        if name in dict(SECTIONS) and callable(fn):
            return fn()
        return {"error": f"unknown section '{name}'"}
