"""Model router: DeepSeek default + Nemotron fallback/selection (no network)."""

from providers.model_router import COMPLEX_TASK_TYPES, ModelRouter
from providers.nemotron_provider import NemotronProvider

KEYS = ("NEMOTRON_ENABLED", "NEMOTRON_API_KEY", "NEMOTRON_BASE_URL", "NEMOTRON_MODEL")


def _clear_nemotron(monkeypatch):
    for k in KEYS:
        monkeypatch.delenv(k, raising=False)


def test_deepseek_is_default_for_routine_work(monkeypatch):
    _clear_nemotron(monkeypatch)
    r = ModelRouter(config=None)
    for task in ("research", "content", "summary", "logs", "general"):
        provider, _model = r.select(task, "normal")
        assert provider == "deepseek"


def test_complex_task_falls_back_to_deepseek_when_nemotron_disabled(monkeypatch):
    _clear_nemotron(monkeypatch)  # NEMOTRON_ENABLED unset -> disabled
    r = ModelRouter(config=None)
    for task in sorted(COMPLEX_TASK_TYPES):
        provider, _ = r.select(task, "complex")
        assert provider == "deepseek"  # graceful fallback


def test_nemotron_selected_when_enabled_and_configured(monkeypatch):
    _clear_nemotron(monkeypatch)
    monkeypatch.setenv("NEMOTRON_ENABLED", "true")
    monkeypatch.setenv("NEMOTRON_API_KEY", "nk-test")
    monkeypatch.setenv("NEMOTRON_BASE_URL", "http://localhost:8000/v1")
    r = ModelRouter(config=None)
    assert r.nemotron_available() is True
    provider, _ = r.select("reasoning", "complex")
    assert provider == "nemotron"
    # Routine work still uses DeepSeek even when Nemotron is available.
    assert r.select("research", "normal")[0] == "deepseek"


def test_nemotron_provider_disabled_by_default(monkeypatch):
    _clear_nemotron(monkeypatch)
    p = NemotronProvider(config=None)
    assert p.enabled() is False
    assert p.available() is False


def test_mock_mode_complete_has_no_spend(monkeypatch, tmp_path):
    _clear_nemotron(monkeypatch)
    from providers.model_router import CostTracker
    r = ModelRouter(config=None, cost_tracker=CostTracker(tmp_path / "ledger.json"))
    res = r.complete("summarize this", task_type="research", complexity="normal")
    assert res.is_mock is True
    assert res.needs_approval is False
    assert r.cost_tracker.month_total() == 0.0  # mock never spends
