"""OpenAI provider (live calls only in live mode, with a key present).

The ``openai`` SDK is imported lazily so it is not a hard dependency. If it is missing
or no key is set, :class:`LLMNotConfigured` is raised and the router falls back to mock.
"""

from __future__ import annotations

from typing import Optional

from core.providers.base import LLMNotConfigured, LLMProvider, LLMResponse


class OpenAIProvider(LLMProvider):
    name = "openai"
    key_env = "OPENAI_API_KEY"
    default_model = "gpt-4o-mini"

    def complete(self, prompt: str, *, system: Optional[str] = None, model: Optional[str] = None) -> LLMResponse:
        key = self.api_key()
        if not key:
            raise LLMNotConfigured("OPENAI_API_KEY is not set")
        try:
            from openai import OpenAI  # lazy import
        except ImportError as exc:
            raise LLMNotConfigured("openai SDK not installed (pip install openai)") from exc

        model = model or self.default_model
        client = OpenAI(api_key=key)
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        resp = client.chat.completions.create(model=model, messages=messages)
        text = resp.choices[0].message.content or ""
        return LLMResponse(text=text, provider=self.name, model=model, raw=resp)
