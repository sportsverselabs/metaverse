"""Provider interface and shared response type."""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional

from core.logging_setup import get_logger


class LLMNotConfigured(RuntimeError):
    """Raised when a live call is attempted but the key or SDK is missing.

    The router catches this and falls back to mock — so a missing key never crashes
    the system.
    """


@dataclass
class LLMResponse:
    text: str
    provider: str
    model: str
    is_mock: bool = False
    raw: Any = field(default=None, repr=False)


class LLMProvider(ABC):
    """Base class for all providers.

    Subclasses set ``name``, ``key_env`` (the ``.env`` variable holding the key), and
    ``default_model``. Keys are ALWAYS read from the environment/``.env`` — never
    hard-coded and never logged.
    """

    name: str = "base"
    key_env: Optional[str] = None
    default_model: str = ""

    def __init__(self, config=None, logger=None) -> None:
        self.config = config
        self.log = logger or get_logger(f"llm.{self.name}")

    def api_key(self) -> Optional[str]:
        """Read this provider's key from config/.env. Returns None if absent."""
        if not self.key_env:
            return None
        if self.config is not None:
            return self.config.secret(self.key_env)
        return os.environ.get(self.key_env)

    def available(self) -> bool:
        """True if this provider has a key configured (does not check the SDK)."""
        return bool(self.api_key())

    @abstractmethod
    def complete(self, prompt: str, *, system: Optional[str] = None, model: Optional[str] = None) -> LLMResponse:
        """Return a completion. Real providers raise :class:`LLMNotConfigured` if unusable."""
        raise NotImplementedError
