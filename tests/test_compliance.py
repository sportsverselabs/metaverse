"""Tests for the Compliance skeleton and the workflow approval gate.

These lock in the most important safety guarantee for Phase 1: nothing public-facing is
auto-approved, and workflow steps that require approval are blocked without it.
"""

from agents.compliance import Compliance, VERDICT_NEEDS_HUMAN
from agents.base import STATUS_BLOCKED, Task
from workflows.runner import Step, Workflow, WorkflowRunner


def test_compliance_never_auto_approves():
    comp = Compliance()
    result = comp.review("Some draft caption with an affiliate link", platform="instagram")
    assert result.approved is False
    assert result.verdict == VERDICT_NEEDS_HUMAN
    # Every required dimension is present and pending.
    assert set(result.checks) >= {"copyright", "ftc_disclosure", "brand_safety"}


def test_compliance_handle_blocks():
    comp = Compliance()
    result = comp.handle(Task(name="review", payload={"content": "x", "platform": "tiktok"}))
    assert result.status == STATUS_BLOCKED


def test_workflow_approval_gate_blocks():
    comp = Compliance()
    runner = WorkflowRunner(agents={"compliance": comp})
    wf = Workflow(
        name="publish_clip",
        steps=[Step(name="public_post", agent="compliance", task="review", requires_approval=True)],
    )
    # No approvals granted -> the gated step is blocked and the run stops there.
    results = runner.run(wf, approvals=set())
    assert results[0].status == STATUS_BLOCKED
    assert "human approval" in results[0].detail


# --- Deepened per-dimension checks (Phase 4 follow-up) -------------------------
def test_benign_content_passes_all_checks():
    comp = Compliance()
    r = comp.review_draft("Here is a clean draft brief with bullet points about the season.")
    assert r.passed is True
    assert r.risk_score == 0
    assert all(v == "pass" for v in r.checks.values())
    assert r.verdict == VERDICT_NEEDS_HUMAN  # still never auto-approves


def test_copyright_flag_blocks_compliance_gate():
    comp = Compliance()
    r = comp.review_draft("Use the official broadcast footage from ESPN of the full match.")
    assert r.checks["copyright"] == "flag"
    assert r.passed is False  # critical flag fails Gate 3 even if score were low


def test_affiliate_without_disclosure_flags_ftc():
    comp = Compliance()
    r = comp.review_draft("Buy now using my promo code to support the channel!")
    assert r.checks["affiliate_disclosure"] == "flag"
    assert r.checks["ftc_disclosure"] == "flag"
    assert r.passed is False


def test_per_platform_review_warns_on_music():
    comp = Compliance()
    r = comp.review_draft("Add a trending sound / copyrighted music track under the clip.")
    for dim in ("youtube_review", "tiktok_review", "instagram_review"):
        assert r.checks[dim] == "warn"
