"""LLM router.

Single choke-point for language-model calls. Agents call ``router.complete(...)`` and
never touch a provider SDK directly. The router:

- defaults to **mock mode** (no network) — set ``LLM_MODE=live`` in ``.env`` to enable real calls;
- routes a task type to a (provider, model) pair;
- falls back to mock — never crashes — if a key or SDK is missing in live mode.

Supported providers: ``mock`` (default), ``openai``, ``anthropic``, ``deepseek``.
Keys are read only from ``.env`` (via Config), never hard-coded.
"""

from __future__ import annotations

from typing import Optional

from core.logging_setup import get_logger
from core.providers import (
    AnthropicProvider,
    DeepSeekProvider,
    LLMNotConfigured,
    LLMResponse,
    MockProvider,
    OpenAIProvider,
)

__all__ = ["LLMRouter", "LLMResponse", "LLMNotConfigured", "DEFAULT_ROUTES"]

# task type -> (provider name, model). Tune per cost/quality once providers are live.
DEFAULT_ROUTES: dict[str, tuple[str, str]] = {
    "general": ("anthropic", "claude-sonnet-4-6"),
    "reasoning": ("anthropic", "claude-opus-4-8"),
    "research": ("deepseek", "deepseek-chat"),
    "cheap": ("openai", "gpt-4o-mini"),
}


class LLMRouter:
    def __init__(self, config=None, mode: Optional[str] = None, routes=None, logger=None) -> None:
        self.config = config
        self.log = logger or get_logger("llm")
        configured_mode = mode or (config.get("LLM_MODE") if config else None) or "mock"
        self.mode = str(configured_mode).lower()
        self.routes = dict(routes or DEFAULT_ROUTES)
        # One instance of each provider; all read keys lazily from .env.
        self._providers: dict[str, object] = {
            p.name: p
            for p in (
                MockProvider(config),
                OpenAIProvider(config),
                AnthropicProvider(config),
                DeepSeekProvider(config),
            )
        }

    # ------------------------------------------------------------------ #
    @property
    def providers(self) -> list[str]:
        return sorted(self._providers)

    @property
    def is_live(self) -> bool:
        return self.mode == "live"

    # Preference order when auto-detecting which real provider to use in live mode.
    _REAL_PREFERENCE = ("anthropic", "openai", "deepseek")

    def available_providers(self) -> list[str]:
        """Provider names that currently have a key configured (mock is always available)."""
        return sorted(n for n, p in self._providers.items() if p.available())

    def route(self, task_type: str = "general") -> tuple[str, str]:
        return self.routes.get(task_type, self.routes["general"])

    def get_provider(self, name: str):
        return self._providers.get(name)

    def _first_available_real(self):
        """Return the first real (non-mock) provider that has a key, or None."""
        for name in self._REAL_PREFERENCE:
            prov = self._providers.get(name)
            if prov is not None and prov.available():
                return prov
        return None

    # ------------------------------------------------------------------ #
    def complete(
        self,
        prompt: str,
        *,
        task_type: str = "general",
        system: Optional[str] = None,
        provider: Optional[str] = None,
    ) -> LLMResponse:
        """Return a completion. Mock by default; live only when ``LLM_MODE=live`` and a key exists."""
        mock = self._providers["mock"]

        # Default safe path: never call the network.
        if not self.is_live:
            self.log.info("LLM complete (mock mode): task=%s", task_type)
            return mock.complete(prompt, system=system, model=self.route(task_type)[1])

        # Live mode: choose a provider, but degrade gracefully to mock on any problem.
        # Preference: explicit arg > config LLM_PROVIDER > task route > any available real key.
        if provider:
            pname, model = provider, None
        elif self.config is not None and self.config.get("LLM_PROVIDER"):
            pname, model = str(self.config.get("LLM_PROVIDER")).lower(), None
        else:
            pname, model = self.route(task_type)

        prov = self._providers.get(pname)
        if prov is None or not prov.available():
            # Auto-detect: use whichever single real key the owner actually configured.
            alt = self._first_available_real()
            if alt is None:
                self.log.warning("No live provider key found (tried '%s'); using mock.", pname)
                return mock.complete(prompt, system=system, model=model)
            self.log.info("Provider '%s' unavailable; auto-selected '%s' (key present).", pname, alt.name)
            prov, model = alt, None

        try:
            self.log.info("LLM complete (live): provider=%s task=%s", prov.name, task_type)
            return prov.complete(prompt, system=system, model=model)
        except LLMNotConfigured as exc:
            self.log.warning("Provider '%s' not usable (%s); using mock.", prov.name, exc)
        except Exception as exc:  # network/SDK errors must never crash the system
            self.log.error("Provider '%s' error (%s); using mock.", prov.name, exc)
        return mock.complete(prompt, system=system, model=model)
