"""Tests for Phase 4→5 agents: approval agent, video agent, Telegram dispatch, reporting, dashboard."""

import pytest

from agents.approval_agent import ApprovalAgent
from agents.video_agent import VideoAgent
from approval.approval_queue import ApprovalQueue
from integrations.telegram_bot import HELP, JarvisTelegramBot
from memory.manager import MemoryManager
from orchestration.state import OrchestrationState
from providers.model_router import ModelRouter
from review.models import STATUS_OWNER_APPROVED, STATUS_SCHEDULED, make_review_item
from review.service import ReviewError, ReviewService
from review.store import ReviewStore


def _approval_agent(tmp_path):
    mem = MemoryManager(store_dir=tmp_path / "mem")
    rs = ReviewStore(base_dir=tmp_path / "review")
    agent = ApprovalAgent(review_service=ReviewService(rs, memory=mem),
                          approval_queue=ApprovalQueue(base_dir=tmp_path / "ap", memory=mem), memory=mem)
    return agent, rs


def test_approval_agent_approve(tmp_path):
    agent, rs = _approval_agent(tmp_path)
    item = make_review_item("content_agent", "draft body", 0, {"passed": True, "risk_score": 0})
    rs.add(item)
    out = agent.approve(item.id)
    assert out.status == STATUS_OWNER_APPROVED
    assert out.published is False


def test_confirm_publish_requires_are_you_sure(tmp_path):
    agent, rs = _approval_agent(tmp_path)
    item = make_review_item("content_agent", "clean draft", 0, {"passed": True, "risk_score": 0},
                            compliance_passed=True)
    rs.add(item)
    with pytest.raises(ReviewError):
        agent.confirm_publish(item.id)                  # no confirmation
    out = agent.confirm_publish(item.id, are_you_sure=True)
    assert out.status == STATUS_SCHEDULED
    assert out.published is False                        # scheduling != publishing


def test_upload_edited_version(tmp_path):
    agent, rs = _approval_agent(tmp_path)
    item = make_review_item("content_agent", "original draft", 0, {"passed": True}, compliance_passed=True)
    rs.add(item)
    out = agent.upload_edited_version(item.id, "my hand-edited final version")
    assert "hand-edited" in out.content
    assert out.status == STATUS_OWNER_APPROVED


def test_video_agent_drafts_with_capcut_note():
    va = VideoAgent(ModelRouter(config=None))  # mock mode
    st = OrchestrationState(user_request="make a video about a buzzer beater")
    st.task_type = "video"
    va.run(st)
    assert st.output
    assert "CapCut" in st.output


def test_telegram_help_unknown_and_noncommand():
    bot = JarvisTelegramBot()
    assert "/status" in bot.dispatch("/help")
    assert "Unknown" in bot.dispatch("/nope")
    assert "command" in bot.dispatch("hello").lower()
    # There is NO bare /publish command that posts.
    assert "Unknown" in bot.dispatch("/publish")


def test_telegram_send_is_dry_run_without_token():
    bot = JarvisTelegramBot()
    bot._token = None
    res = bot.send("hi")
    assert res["sent"] is False


def test_telegram_authorization():
    bot = JarvisTelegramBot()
    bot._chat_id = "123"
    assert bot.dispatch("/help", from_chat_id="999") == "Unauthorized."
    assert "/status" in bot.dispatch("/help", from_chat_id="123")


def test_reports_build_text():
    from reporting.reports import build_daily_report, build_weekly_report
    assert "DAILY REPORT" in build_daily_report()
    assert "WEEKLY REPORT" in build_weekly_report()


def test_dashboard_render_and_assemble():
    from agents.dashboard_agent import DashboardAgent
    from dashboard.render import render_html
    data = DashboardAgent().assemble_data()
    for key in ("system_status", "pending_approvals", "content_calendar", "agent_activity", "owner_todo", "cost"):
        assert key in data
    html = render_html(data)
    assert "SportVerse Labs" in html and "<html" in html.lower()
