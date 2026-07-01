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
    ("pipeline", "Content Pipeline"), ("video", "Creative Studio"), ("publishing", "Publishing"),
    ("analytics", "Analytics"), ("reports", "Reports"), ("agents", "Agents"),
    ("skills", "Skills"), ("sports", "Sports Data"),
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
        self._sports_hub = None
        self._publishing_service = None

    @property
    def sports_hub(self):
        # Built lazily: avoids network/Telegram setup unless the Sports Data page is opened.
        if self._sports_hub is None:
            from sports.hub import SportsDataHub
            self._sports_hub = SportsDataHub(config=self.config)
        return self._sports_hub

    @property
    def publishing_service(self):
        # Built lazily: avoids platform adapter setup unless the Publishing page is opened.
        if self._publishing_service is None:
            from publishing.service import PublishingService
            self._publishing_service = PublishingService(config=self.config)
        return self._publishing_service


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
        apifootball = bool(c.secret("API_FOOTBALL_KEY"))
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
            {"name": "ESPN", "state": "ok", "status": "online (keyless)"},
            {"name": "API-Football", "state": "ok" if apifootball else "warn",
             "status": "live" if apifootball else "needs API key"},
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
        # Cross-check gated actions against real draft/review records; flag orphans (needs-repair).
        try:
            from review.reconcile import audit_actions
            actions = audit_actions(review_store=self.dash.review_store)
        except Exception:
            actions = d["pending_approvals"]["actions"]
        return {"content": d["pending_approvals"]["content"], "actions": actions,
                "orphaned": sum(1 for a in actions if a.get("orphaned"))}

    def pipeline(self) -> dict:
        from review.models import (STATUS_OWNER_APPROVED, STATUS_PUBLISHED, STATUS_READY, STATUS_REJECTED,
                                    STATUS_REVISION, STATUS_SCHEDULED)
        rs = self.dash.review_store
        pending_actions = len(self.dash.approval_queue.list(status="pending"))
        try:
            from review.reconcile import find_orphaned
            orphaned = len(find_orphaned(review_store=rs))
        except Exception:
            orphaned = 0
        return {"stages": [
            {"stage": "Idea / Researching", "count": "—", "note": "tasks are synchronous; see journal"},
            {"stage": "Drafting → Waiting approval", "count": len(rs.list(status=STATUS_READY))},
            {"stage": "Needs edit (revision)", "count": len(rs.list(status=STATUS_REVISION))},
            {"stage": "Owner approved", "count": len(rs.list(status=STATUS_OWNER_APPROVED))},
            {"stage": "Scheduled", "count": len(rs.list(status=STATUS_SCHEDULED))},
            {"stage": "Rejected", "count": len(rs.list(status=STATUS_REJECTED, include_archived=True))},
            {"stage": "Published", "count": len(rs.list(status=STATUS_PUBLISHED)), "note": "explicit publisher only"},
        ], "gated_actions_pending": pending_actions, "gated_actions_orphaned": orphaned,
            "note": ("Gated actions live in the Approvals tab (separate from content drafts). "
                     + (f"{orphaned} orphaned action(s) need repair: run `python -m review reconcile --apply`."
                        if orphaned else "No orphaned actions."))}

    def video(self) -> dict:
        # Rendered by dashboard.studio.overview_html() (Creative Studio V1b); data handled there.
        return {"studio": True}

    def publishing(self) -> dict:
        c = self.config
        social = {row["platform"]: row for row in self.publishing_service.connection_statuses()}
        email = bool(c.secret("EMAIL_APP_PASSWORD") and c.get("EMAIL_ADDRESS"))
        from review.models import STATUS_OWNER_APPROVED, STATUS_SCHEDULED
        rs = self.dash.review_store
        publishable = rs.list(status=STATUS_OWNER_APPROVED) + rs.list(status=STATUS_SCHEDULED)
        youtube_connected = bool(social["youtube"]["configured"])
        tiktok_connected = bool(social["tiktok"]["configured"])
        instagram_connected = bool(social["instagram"]["configured"])
        publish_targets = [
            {
                "platform": "youtube",
                "label": "YouTube",
                "visibility": "private",
                "button": "YouTube private",
                "enabled": youtube_connected,
                "note": "Ready: uploads start private on Platinum Clips."
                if youtube_connected else "Needs YouTube OAuth credentials.",
            },
            {
                "platform": "tiktok",
                "label": "TikTok",
                "visibility": "draft",
                "button": "TikTok draft",
                "enabled": tiktok_connected,
                "note": "Pending: TikTok developer app/OAuth still needs setup.",
            },
            {
                "platform": "instagram",
                "label": "Instagram",
                "visibility": "test",
                "button": "Instagram test",
                "enabled": instagram_connected,
                "note": "Pending: Meta/Instagram business token still needs setup.",
            },
        ]
        return {"connections": [
            {"platform": "Website", "status": "connected", "state": "ok",
             "detail": "sportsversenews.com is live."},
            {"platform": "Telegram bot", "status": "connected" if c.secret("TELEGRAM_BOT_TOKEN") else "needs setup",
             "state": "ok" if c.secret("TELEGRAM_BOT_TOKEN") else "warn",
             "detail": "Owner alerts and dashboard 2FA." if c.secret("TELEGRAM_BOT_TOKEN")
             else "Add TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID in server .env."},
            {"platform": "Email (Gmail)", "status": "connected" if email else "needs setup",
             "state": "ok" if email else "warn",
             "detail": "Gmail app password configured." if email else "Needs Gmail App Password."},
            {"platform": "YouTube", "status": "connected" if youtube_connected else "needs setup",
             "state": "ok" if youtube_connected else "warn",
             "detail": "Private uploads enabled for Platinum Clips." if youtube_connected
             else "Needs YOUTUBE_CLIENT_ID / SECRET / REFRESH_TOKEN."},
            {"platform": "TikTok", "status": "pending setup" if not tiktok_connected else "connected",
             "state": "warn" if not tiktok_connected else "ok",
             "detail": "Needs TikTok developer app, callback, and OAuth token before draft uploads."
             if not tiktok_connected else "Draft/inbox uploads enabled."},
            {"platform": "Instagram", "status": "pending setup" if not instagram_connected else "connected",
             "state": "warn" if not instagram_connected else "ok",
             "detail": "Needs Meta app review/business token before test publishing."
             if not instagram_connected else "Instagram test publishing enabled."},
        ], "publishable": [
            {"id": i.id, "skill": i.skill, "status": i.status}
            for i in publishable
        ], "publish_targets": publish_targets,
            "history": self.publishing_service.history(limit=10),
            "note": "Publishing is live-gated. YouTube is connected for private uploads; Instagram and TikTok stay pending until their owner setup is complete."}

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
        return {"docs": ["docs/ARCHITECTURE.md", "docs/SPORTS_DATA_HUB.md", "docs/DASHBOARD_GUIDE.md",
                         "docs/USER_MANUAL.md", "docs/AGENT_DIRECTORY.md", "docs/DEPLOYMENT_GUIDE.md",
                         "docs/ACCOUNT_INVENTORY.md", "docs/MEDIA_LICENSE_POLICY.md", "docs/MASTER_AUDIT.md",
                         "docs/ARCHITECTURE_AUDIT.md", "docs/PHASE5_SETUP.md", "docs/RECOVERY_GUIDE.md"],
                "agents": [{"name": k, "purpose": v} for k, v in AGENT_DIRECTORY.items()]}

    def sports(self) -> dict:
        # Defensive: the Sports Data Hub serves stale data on provider failure, but never crash the page.
        try:
            from sports.espn_client import LEAGUES
            hub = self.sports_hub
            football_live = hub.football_live() if hub.football_configured() else {"ok": False, "data": []}
            football_status = hub.football_status() if hub.football_configured() else {"ok": False, "data": None}
            return {
                "providers": hub.providers_status(),
                "live_games": hub.live_games(),
                "upcoming_games": hub.upcoming_games()[:12],
                "latest_news": hub.latest_news(per_league=2)[:12],
                "football_live": (football_live.get("data") or [])[:12],
                "football_status": football_status.get("data"),
                "leagues": list(LEAGUES),
            }
        except Exception as exc:  # pragma: no cover - safety net
            self.log.error("sports section failed: %s", type(exc).__name__)
            return {"error": f"sports data unavailable ({type(exc).__name__})",
                    "providers": {}, "live_games": [], "upcoming_games": [], "latest_news": []}

    def skills(self) -> dict:
        import json
        from pathlib import Path
        installed = []
        try:
            allow = json.loads(Path("config/openclaw_allowlist.json").read_text(encoding="utf-8"))
            for name, spec in (allow.get("skills") or {}).items():
                if spec.get("allowed"):
                    installed.append({"skill": name, "version": "1.0", "status": "active",
                                      "risk": spec.get("risk", "low"),
                                      "capabilities": ", ".join(spec.get("capabilities", [])),
                                      "agent": "OpenClaw registry"})
        except Exception:
            pass
        # External skills requested in the master plan — honest "not installed yet" status.
        pending = [
            {"skill": "last30days-skill", "status": "not installed (pending review)",
             "purpose": "Trend discovery (Reddit/X/YouTube/web)", "agent": "Research Agent"},
            {"skill": "taste-skill", "status": "not installed (pending review)",
             "purpose": "Improve dashboard/website quality (typography, spacing, motion)", "agent": "Dashboard/Frontend"},
            {"skill": "open-notebook", "status": "not installed (pending review)",
             "purpose": "Research memory / article & idea storage (Hermes-searchable)", "agent": "Hermes"},
        ]
        return {"installed": installed, "pending": pending,
                "note": "Installed skills are draft-only OpenClaw skills (no secrets/shell/publish). "
                        "External skills require license/safety review + owner approval before install."}

    def section(self, name: str) -> dict:
        fn = getattr(self, name, None)
        if name in dict(SECTIONS) and callable(fn):
            return fn()
        return {"error": f"unknown section '{name}'"}
