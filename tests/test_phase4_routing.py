"""Hermes routing + Jarvis classification."""

from agents.hermes import Hermes
from agents.jarvis import Jarvis
from orchestration.state import OrchestrationState


def test_hermes_routes_task_types_to_nodes():
    h = Hermes()
    assert h.route_task("research") == "research_agent"
    assert h.route_task("content") == "content_agent"
    assert h.route_task("coding") == "coding_agent"
    assert h.route_task("reasoning") == "nemotron_reasoning_agent"
    assert h.route_task("compliance") == "compliance_agent"
    assert h.route_task("skill") == "openclaw_skill_agent"
    assert h.route_task("something_unknown") == "research_agent"  # safe default


def test_hermes_decide_sets_route_and_flags_gated():
    h = Hermes()
    st = OrchestrationState(user_request="publish this to instagram")
    st.task_type = "content"
    st.gated_actions = ["public_post"]
    h.decide(st)
    assert st.route == "content_agent"
    assert any("public_post" in r for r in st.approval_reasons)


def test_jarvis_classifies_task_types():
    j = Jarvis()
    assert j.parse("draft a video script about the finals")["task_type"] == "content"
    assert j.parse("research trending NBA storylines")["task_type"] == "research"
    assert j.parse("refactor this function and add a unit test")["task_type"] == "coding"
    plan = j.parse("design the system architecture and strategy")
    assert plan["task_type"] == "reasoning"
    assert plan["complexity"] == "complex"


def test_jarvis_flags_gated_actions_as_high_risk():
    j = Jarvis()
    parsed = j.parse("publish this and post on tiktok")
    assert parsed["risk"] == "high"
    assert "public_post" in parsed["gated_actions"] or "publish_content" in parsed["gated_actions"]


def test_jarvis_does_not_decide_route():
    # Jarvis only classifies; it returns no 'route' field (Hermes decides routing).
    j = Jarvis()
    parsed = j.parse("research something")
    assert "route" not in parsed
