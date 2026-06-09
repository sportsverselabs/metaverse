"""Cost tracking + budget gating."""

from providers.model_router import CostTracker, ModelRouter


def test_cost_tracker_accumulates(tmp_path):
    t = CostTracker(tmp_path / "ledger.json")
    assert t.month_total() == 0.0
    t.add(0.01)
    t.add(0.02)
    assert round(t.month_total(), 4) == 0.03


def test_estimate_cost_positive_for_real_tokens():
    r = ModelRouter(config=None)
    tokens = r.estimate_tokens("a fairly long prompt " * 50)
    assert tokens > 0
    assert r.estimate_cost("deepseek", tokens) > 0


def test_over_threshold_routes_to_approval_without_spending(tmp_path):
    budget = {
        "monthly_budget_usd": 100.0,
        "per_task_approval_threshold_usd": 0.0001,  # tiny -> any real task trips it
        "assumed_completion_tokens": 600,
        "prices_per_1k_tokens": {"deepseek": {"input": 0.001, "output": 0.01}},
    }
    r = ModelRouter(config=None, budget=budget, cost_tracker=CostTracker(tmp_path / "ledger.json"))
    res = r.complete("write a long analysis " * 20, task_type="research")
    assert res.needs_approval is True
    assert res.text == ""                       # nothing generated
    assert r.cost_tracker.month_total() == 0.0  # nothing spent


def test_monthly_budget_blocks_when_exhausted(tmp_path):
    budget = {
        "monthly_budget_usd": 0.0005,
        "per_task_approval_threshold_usd": 100.0,  # per-task ok, but monthly is tiny
        "assumed_completion_tokens": 600,
        "prices_per_1k_tokens": {"deepseek": {"input": 0.001, "output": 0.01}},
    }
    tracker = CostTracker(tmp_path / "ledger.json")
    r = ModelRouter(config=None, budget=budget, cost_tracker=tracker)
    res = r.complete("hello", task_type="research")
    assert res.needs_approval is True
