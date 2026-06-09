"""DeepSeek provider (Phase 4 path).

Single source of truth lives in ``core.providers.deepseek_provider``; this module re-exports it
so the Phase-4 requested path ``providers/deepseek_provider.py`` resolves without duplicating
the implementation. DeepSeek is OpenAI-compatible and uses the ``openai`` SDK.
"""

from __future__ import annotations

from core.providers.deepseek_provider import DeepSeekProvider  # noqa: F401

__all__ = ["DeepSeekProvider"]
