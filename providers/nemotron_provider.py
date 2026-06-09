"""NVIDIA Nemotron / NeMo provider adapter (optional).

Pluggable through the standard ``LLMProvider`` interface so it can be served via a hosted API,
a local endpoint, an NVIDIA NIM container, or a future provider — without changing any agent.
NVIDIA NIM exposes an OpenAI-compatible API, so this reuses the ``openai`` SDK pointed at
``NEMOTRON_BASE_URL``.

Disabled by default (``NEMOTRON_ENABLED=false``). When disabled or unavailable, the model
router falls back to DeepSeek. Keys are read only from ``.env``; never hard-coded or logged.
"""

from __future__ import annotations

from typing import Optional

from core.providers.base import LLMNotConfigured, LLMProvider, LLMResponse

_TRUTHY = {"1", "true", "yes", "on"}
DEFAULT_MODEL = "nvidia/llama-3.1-nemotron-70b-instruct"


class NemotronProvider(LLMProvider):
    name = "nemotron"
    key_env = "NEMOTRON_API_KEY"
    default_model = DEFAULT_MODEL

    def _cfg(self, key: str, default: Optional[str] = None) -> Optional[str]:
        if self.config is not None:
            return self.config.get(key, default)
        import os
        return os.environ.get(key, default)

    def enabled(self) -> bool:
        return str(self._cfg("NEMOTRON_ENABLED", "false")).strip().lower() in _TRUTHY

    def base_url(self) -> Optional[str]:
        return self._cfg("NEMOTRON_BASE_URL") or None

    def model_name(self) -> str:
        return self._cfg("NEMOTRON_MODEL") or self.default_model

    def available(self) -> bool:
        """Usable only if explicitly enabled AND a key + base URL are configured."""
        return bool(self.enabled() and self.api_key() and self.base_url())

    def complete(self, prompt: str, *, system: Optional[str] = None, model: Optional[str] = None) -> LLMResponse:
        if not self.enabled():
            raise LLMNotConfigured("Nemotron is disabled (NEMOTRON_ENABLED=false)")
        key = self.api_key()
        base = self.base_url()
        if not key or not base:
            raise LLMNotConfigured("NEMOTRON_API_KEY and NEMOTRON_BASE_URL must be set")
        try:
            from openai import OpenAI  # NIM is OpenAI-compatible
        except ImportError as exc:
            raise LLMNotConfigured("openai SDK not installed (required for Nemotron via NIM)") from exc

        model = model or self.model_name()
        client = OpenAI(api_key=key, base_url=base)
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        resp = client.chat.completions.create(model=model, messages=messages)
        text = resp.choices[0].message.content or ""
        return LLMResponse(text=text, provider=self.name, model=model, raw=resp)
