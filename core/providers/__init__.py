"""LLM provider abstraction.

One small class per provider, all behind a common :class:`~core.providers.base.LLMProvider`
interface so the rest of the system never imports a vendor SDK directly. The default
provider is :class:`~core.providers.mock.MockProvider`, which performs NO network calls.

Real providers (OpenAI / Anthropic / DeepSeek) lazily import their SDK only when actually
called in live mode with a key present — so the skeleton runs with zero installs and never
contacts a paid service by accident.
"""

from core.providers.base import LLMNotConfigured, LLMProvider, LLMResponse  # noqa: F401
from core.providers.mock import MockProvider  # noqa: F401
from core.providers.openai_provider import OpenAIProvider  # noqa: F401
from core.providers.anthropic_provider import AnthropicProvider  # noqa: F401
from core.providers.deepseek_provider import DeepSeekProvider  # noqa: F401

__all__ = [
    "LLMProvider",
    "LLMResponse",
    "LLMNotConfigured",
    "MockProvider",
    "OpenAIProvider",
    "AnthropicProvider",
    "DeepSeekProvider",
]
