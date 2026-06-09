"""Mock provider — the default. Performs NO network calls."""

from __future__ import annotations

from typing import Optional

from core.providers.base import LLMProvider, LLMResponse


class MockProvider(LLMProvider):
    name = "mock"
    default_model = "mock-1"

    def available(self) -> bool:  # always usable
        return True

    def complete(self, prompt: str, *, system: Optional[str] = None, model: Optional[str] = None) -> LLMResponse:
        model = model or self.default_model
        preview = " ".join((prompt or "").split())
        if len(preview) > 240:
            preview = preview[:240] + "..."
        text = (
            "[MOCK RESPONSE] Dry-run mode: no live model was called. "
            "This is a deterministic placeholder draft generated offline. "
            f"(model={model}) Prompt preview: {preview}"
        )
        self.log.info("Mock completion produced (no network).")
        return LLMResponse(text=text, provider=self.name, model=model, is_mock=True)
