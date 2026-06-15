"""Tests for the dashboard UI rendering + data layer (no server/network needed)."""

from dashboard import app as ui
from dashboard.data import SECTIONS, DashboardData


def test_login_and_verify_pages():
    assert "Sign in" in ui.login_page() or "sign-in" in ui.login_page().lower()
    assert "SPORTS" in ui.login_page()
    assert "code" in ui.verify_page().lower()


def test_shell_lists_all_14_sections():
    shell = ui.shell_page("owner")
    assert len(SECTIONS) == 14
    for key, label in SECTIONS:
        assert f"data-section='{key}'" in shell
        assert label in shell


def test_statuses_cover_required_components():
    names = " ".join(s["name"] for s in DashboardData().statuses())
    for needle in ("Hermes", "Jarvis", "VPS", "Website", "Telegram", "Email",
                   "DeepSeek", "Nemotron", "LangGraph", "OpenClaw"):
        assert needle in names


def test_render_each_section_returns_html():
    d = DashboardData()
    for key, _label in SECTIONS:
        frag = ui.render_section(key, d)
        assert "<h2>" in frag  # every section renders a heading


def test_home_section_has_metrics_and_status():
    frag = ui.render_section("home", DashboardData())
    assert "Components" in frag and "cost" in frag.lower()
