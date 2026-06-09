"""Anthropic (Claude) provider (live calls only in live mode, with a key present).

The ``anthropic`` SDK is imported lazily. Missing SDK or key -> :class:`LLMNotConfigured`,
which the router handles by falling back to mock.
"""

from __future__ import annotations

from typing import Optional

from core.providers.base import LLMNotConfigured, LLMProvider, LLMResponse


class AnthropicProvider(LLMProvider):
    name = "anthropic"
    key_env = "ANTHROPIC_API_KEY"
    default_model = "claude-sonnet-4-6"

    def complete(self, prompt: str, *, system: Optional[str] = None, model: Optional[str] = None) -> LLMResponse:
        key = self.api_key()
        if not key:
            raise LLMNotConfigured("ANTHROPIC_API_KEY is not set")
        try:
            import anthropic  # lazy import
        except ImportError as exc:
            raise LLMNotConfigured("anthropic SDK not installed (pip install anthropic)") from exc

        model = model or self.default_model
        client = anthropic.Anthropic(api_key=key)
        kwargs = {"model": model, "max_tokens": 1024, "messages": [{"role": "user", "content": prompt}]}
        if system:
            kwargs["system"] = system
        msg = client.messages.create(**kwargs)
        text = "".join(getattr(block, "text", "") for block in msg.content)
        return LLMResponse(text=text, provider=self.name, model=model, raw=msg)
