"""Tests for live-mode LLM routing (with the network mocked) and mock fallback.

We never hit the real network: we monkeypatch the chosen provider's ``complete`` to return
a non-mock response. This proves the router *would* use the real provider when a key exists,
and that a missing key falls back to mock without crashing.
"""

from core.llm_router import LLMRouter
from core.providers.base import LLMResponse

KEYS = ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "DEEPSEEK_API_KEY")


def _clear_keys(monkeypatch):
    for k in KEYS:
        monkeypatch.delenv(k, raising=False)


def test_live_provider_used_when_key_exists(monkeypatch):
    _clear_keys(monkeypatch)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-abc")
    router = LLMRouter(mode="live")

    def fake_complete(prompt, *, system=None, model=None):
        return LLMResponse(text="REAL-ANTHROPIC", provider="anthropic", model=model or "claude", is_mock=False)

    monkeypatch.setattr(router._providers["anthropic"], "complete", fake_complete)
    resp = router.complete("hello", task_type="general")  # 'general' routes to anthropic
    assert resp.is_mock is False
    assert resp.provider == "anthropic"
    assert resp.text == "REAL-ANTHROPIC"


def test_live_autodetects_whichever_key_is_present(monkeypatch):
    _clear_keys(monkeypatch)
    monkeypatch.setenv("DEEPSEEK_API_KEY", "ds-key")  # only DeepSeek configured
    router = LLMRouter(mode="live")

    def fake_complete(prompt, *, system=None, model=None):
        return LLMResponse(text="REAL-DEEPSEEK", provider="deepseek", model="deepseek-chat", is_mock=False)

    monkeypatch.setattr(router._providers["deepseek"], "complete", fake_complete)
    # 'general' routes to anthropic (no key) -> router auto-detects the available deepseek key.
    resp = router.complete("hello", task_type="general")
    assert resp.provider == "deepseek"
    assert resp.is_mock is False


def test_missing_key_falls_back_to_mock_in_live_mode(monkeypatch):
    _clear_keys(monkeypatch)
    router = LLMRouter(mode="live")
    resp = router.complete("hello", task_type="general")
    assert resp.is_mock is True  # no key anywhere -> safe mock fallback, no crash


def test_provider_error_falls_back_to_mock(monkeypatch):
    _clear_keys(monkeypatch)
    monkeypatch.setenv("OPENAI_API_KEY", "key")
    router = LLMRouter(mode="live")

    def boom(prompt, *, system=None, model=None):
        raise RuntimeError("simulated network failure")

    monkeypatch.setattr(router._providers["openai"], "complete", boom)
    resp = router.complete("hello", task_type="cheap")  # 'cheap' routes to openai
    assert resp.is_mock is True  # error is caught; mock fallback, no crash
