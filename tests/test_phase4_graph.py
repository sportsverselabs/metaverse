"""LangGraph state transitions + journal logging + no-publish guarantees (fallback engine)."""

from orchestration.routes import run_fallback
from orchestration.state import OrchestrationState
from review.store import ReviewStore
from tests._phase4_helpers import make_ctx


def test_state_transitions_for_research_task(tmp_path):
    ctx = make_ctx(tmp_path)
    state = OrchestrationState(user_request="research trending NBA storylines")
    run_fallback(state, ctx)
    assert state.path == [
        "jarvis_input", "hermes_router", "cost_router", "research_agent",
        "compliance_agent", "human_approval_gate", "execution_agent",
        "memory_logger", "final_report",
    ]
    assert state.is_mock is True
    assert state.model_provider == "deepseek"
    assert state.final_status == "completed_no_external_action"
    assert state.report  # plain-English report produced


def test_reasoning_task_routes_through_nemotron_node(tmp_path):
    ctx = make_ctx(tmp_path)
    state = OrchestrationState(user_request="design the system architecture and strategy")
    run_fallback(state, ctx)
    assert "nemotron_reasoning_agent" in state.path
    # Nemotron disabled by default -> provider falls back to deepseek.
    assert state.model_provider == "deepseek"


def test_journal_logging_writes_record(tmp_path):
    ctx = make_ctx(tmp_path)
    state = OrchestrationState(user_request="summarize this week's football news")
    run_fallback(state, ctx)
    rows = ctx.journal.read()
    assert len(rows) == 1
    row = rows[0]
    for key in ("task_id", "user_request", "selected_route", "model_used",
                "estimated_tokens", "estimated_cost_usd", "tools_used",
                "approval_status", "final_status"):
        assert key in row
    # Audit trail also recorded.
    assert "orchestrated_task" in ctx.memory.read_audit()


def test_cost_gated_task_skips_worker_and_requests_approval(tmp_path):
    budget = {
        "monthly_budget_usd": 100.0,
        "per_task_approval_threshold_usd": 0.0,  # everything trips the cost gate
        "assumed_completion_tokens": 600,
        "prices_per_1k_tokens": {"deepseek": {"input": 0.001, "output": 0.01}},
    }
    ctx = make_ctx(tmp_path, budget=budget)
    state = OrchestrationState(user_request="research something routine")
    run_fallback(state, ctx)
    # Worker node never ran (no research_agent in path); approval pending; no spend.
    assert "research_agent" not in state.path
    assert state.approval_status == "pending"
    assert ctx.model_router.cost_tracker.month_total() == 0.0


def test_nothing_is_published_anywhere(tmp_path):
    ctx = make_ctx(tmp_path)
    for req in ("research X", "draft a caption", "publish to instagram", "send email to fans"):
        state = OrchestrationState(user_request=req)
        run_fallback(state, ctx)
        assert state.final_status in ("completed_no_external_action", "pending_approval", "blocked_unapproved_skill")
        assert getattr(state, "published", None) in (None, False)


def test_content_draft_is_queued_into_review_surface(tmp_path):
    review_store = ReviewStore(base_dir=tmp_path / "review")
    ctx = make_ctx(tmp_path, review_store=review_store)
    state = OrchestrationState(user_request="draft a punchy caption about the season opener")
    run_fallback(state, ctx)
    assert state.route == "content_agent"
    assert state.final_status == "submitted_to_review"
    assert state.review_id
    # It now appears in the Phase 2 owner-review queue (draft -> review -> schedule).
    assert any(i.id == state.review_id for i in review_store.list_pending())


def test_non_content_routes_are_not_auto_queued(tmp_path):
    review_store = ReviewStore(base_dir=tmp_path / "review")
    ctx = make_ctx(tmp_path, review_store=review_store)
    state = OrchestrationState(user_request="research trending football stories")
    run_fallback(state, ctx)
    assert state.route == "research_agent"
    assert state.final_status == "completed_no_external_action"
    assert state.review_id == ""
    assert review_store.list_pending() == []
