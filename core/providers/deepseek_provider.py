"""DeepSeek provider (live calls only in live mode, with a key present).

DeepSeek exposes an OpenAI-compatible API, so this reuses the ``openai`` SDK pointed at
DeepSeek's base URL. Lazy import; missing SDK or key -> :class:`LLMNotConfigured`.
"""

from __future__ import annotations

from typing import Optional

from core.providers.base import LLMNotConfigured, LLMProvider, LLMResponse


class DeepSeekProvider(LLMProvider):
    name = "deepseek"
    key_env = "DEEPSEEK_API_KEY"
    default_model = "deepseek-chat"
    base_url = "https://api.deepseek.com"

    def complete(self, prompt: str, *, system: Optional[str] = None, model: Optional[str] = None) -> LLMResponse:
        key = self.api_key()
        if not key:
            raise LLMNotConfigured("DEEPSEEK_API_KEY is not set")
        try:
            from openai import OpenAI  # DeepSeek is OpenAI-compatible
        except ImportError as exc:
            raise LLMNotConfigured("openai SDK not installed (required for DeepSeek)") from exc

        model = model or self.default_model
        client = OpenAI(api_key=key, base_url=self.base_url)
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        resp = client.chat.completions.create(model=model, messages=messages)
        text = resp.choices[0].message.content or ""
        return LLMResponse(text=text, provider=self.name, model=model, raw=resp)
