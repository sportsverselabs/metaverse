"""Tests for the dashboard UI rendering + data layer (no server/network needed)."""

from dashboard import app as ui
from dashboard.data import SECTIONS, DashboardData
from sports.cache import SportsCache
from sports.espn_client import ESPNClient
from sports.health import SportsApiHealthMonitor
from sports.hub import SportsDataHub


def _offline_data(tmp_path):
    """A DashboardData whose Sports Hub never touches the network (empty ESPN payloads)."""
    d = DashboardData()
    payload = {"events": [], "articles": []}
    d._sports_hub = SportsDataHub(
        cache=SportsCache(tmp_path / "c.db"),
        espn=ESPNClient(fetch=lambda url: payload),
        health=SportsApiHealthMonitor(state_path=tmp_path / "h.json"),
    )
    return d


def test_login_and_verify_pages():
    assert "Sign in" in ui.login_page() or "sign-in" in ui.login_page().lower()
    assert "SPORTS" in ui.login_page()
    assert "code" in ui.verify_page().lower()


def test_shell_lists_all_16_sections():
    shell = ui.shell_page("owner")
    assert len(SECTIONS) == 16
    for key, label in SECTIONS:
        assert f"data-section='{key}'" in shell
        assert label in shell


def test_statuses_cover_required_components():
    names = " ".join(s["name"] for s in DashboardData().statuses())
    for needle in ("Hermes", "Jarvis", "VPS", "Website", "Telegram", "Email",
                   "DeepSeek", "Nemotron", "LangGraph", "OpenClaw", "ESPN", "API-Football"):
        assert needle in names


def test_render_each_section_returns_html(tmp_path):
    d = _offline_data(tmp_path)
    for key, _label in SECTIONS:
        frag = ui.render_section(key, d)
        assert "<h2>" in frag  # every section renders a heading


def test_sports_and_skills_sections(tmp_path):
    d = _offline_data(tmp_path)
    sports = ui.render_section("sports", d)
    assert "Sports Data" in sports and "Providers" in sports
    skills = ui.render_section("skills", d)
    assert "Skills" in skills and "pending review" in skills.lower()


def test_home_section_has_metrics_and_status():
    frag = ui.render_section("home", DashboardData())
    assert "Components" in frag and "cost" in frag.lower()


def test_publishing_section_shows_youtube_connected_and_pending_platforms():
    frag = ui._r_publishing({
        "note": "Publishing status",
        "connections": [
            {"platform": "YouTube", "status": "connected", "state": "ok",
             "detail": "Private uploads enabled for Platinum Clips."},
            {"platform": "TikTok", "status": "pending setup", "state": "warn",
             "detail": "Needs TikTok developer app."},
            {"platform": "Instagram", "status": "pending setup", "state": "warn",
             "detail": "Needs Meta app review."},
        ],
        "publish_targets": [
            {"platform": "youtube", "label": "YouTube", "visibility": "private",
             "button": "YouTube private", "enabled": True, "note": "Ready."},
            {"platform": "tiktok", "label": "TikTok", "visibility": "draft",
             "button": "TikTok draft", "enabled": False, "note": "Pending."},
            {"platform": "instagram", "label": "Instagram", "visibility": "test",
             "button": "Instagram test", "enabled": False, "note": "Pending."},
        ],
        "publishable": [{"id": "rv1", "skill": "video_project", "status": "owner_approved"}],
        "history": [
            {"ts": "2026-07-01T00:00:00", "review_id": "rv-old", "platform": "youtube",
             "ok": True, "status": "published", "url": "https://youtu.be/example",
             "visibility": "private", "reason": "published"}
        ],
    })
    assert "Private uploads enabled for Platinum Clips." in frag
    assert "dashPublish('rv1','youtube','private')" in frag
    assert "TikTok draft pending" in frag
    assert "Instagram test pending" in frag
    assert frag.count("disabled") >= 2
    assert "Publishing History" in frag
    assert "https://youtu.be/example" in frag
