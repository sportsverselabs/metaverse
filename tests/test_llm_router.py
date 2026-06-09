"""Tests for the LLM router: mock default, graceful degradation, provider set."""

from core.llm_router import LLMRouter


def test_mock_mode_is_default_and_offline(monkeypatch):
    # Ensure no keys are present so we know mock is from mode, not fallback.
    for k in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "DEEPSEEK_API_KEY"):
        monkeypatch.delenv(k, raising=False)
    router = LLMRouter()  # no config -> mode defaults to "mock"
    assert router.mode == "mock"
    resp = router.complete("hello", task_type="general")
    assert resp.is_mock is True
    assert resp.text  # non-empty placeholder


def test_missing_keys_do_not_crash_in_live_mode(monkeypatch):
    for k in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "DEEPSEEK_API_KEY"):
        monkeypatch.delenv(k, raising=False)
    # Live mode but no keys configured: must fall back to mock, never raise.
    router = LLMRouter(mode="live")
    resp = router.complete("hello", task_type="research")
    assert resp.is_mock is True


def test_all_providers_registered():
    router = LLMRouter()
    assert set(router.providers) == {"mock", "openai", "anthropic", "deepseek"}


def test_routes_have_known_providers():
    router = LLMRouter()
    for task_type in ("general", "reasoning", "research", "cheap"):
        provider, model = router.route(task_type)
        assert provider in router.providers
        assert model
