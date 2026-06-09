"""Agent base class and shared task/result types.

Every Sportsverse agent inherits :class:`BaseAgent`. The base encodes the project's
safety policy so individual agents can't accidentally bypass it:

- Agents never publish externally on their own (``can_publish_directly = False``).
- DM/comment replies must use an approved template (enforced in integrations).
- Anything matching the Approval Rules escalates up the chain to the owner.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional

from core.logging_setup import get_logger

# Result status vocabulary
STATUS_OK = "ok"
STATUS_ESCALATED = "escalated"
STATUS_BLOCKED = "blocked"            # blocked by a safety policy (e.g. needs human approval)
STATUS_NOT_IMPLEMENTED = "not_implemented"
STATUS_READY_FOR_REVIEW = "ready_for_owner_review"  # draft completed pipeline; awaiting human approval


@dataclass
class Task:
    """A unit of work handed to an agent."""

    name: str
    payload: dict[str, Any] = field(default_factory=dict)
    requested_by: str = "system"


@dataclass
class AgentResult:
    """The outcome of handling a task."""

    agent: str
    status: str
    detail: str = ""
    data: dict[str, Any] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return self.status == STATUS_OK


class BaseAgent(ABC):
    """Base class for all agents.

    Subclasses set the class attributes (``name``, ``role``, ``reports_to``) and
    implement :meth:`handle`. Shared services (config, memory, llm) are injected so
    the same agent works locally or on a VPS without code changes.
    """

    name: str = "base"
    role: str = "Base agent"
    reports_to: Optional[str] = None

    # --- Safety defaults (do not flip to True without owner approval) ---
    can_publish_directly: bool = False  # external posting always needs human approval

    def __init__(self, *, config=None, memory=None, llm=None, logger=None) -> None:
        self.config = config
        self.memory = memory
        self.llm = llm
        self.log = logger or get_logger(f"agent.{self.name}")

    # ------------------------------------------------------------------ #
    # Subclasses implement this.
    # ------------------------------------------------------------------ #
    @abstractmethod
    def handle(self, task: Task) -> AgentResult:
        """Handle a task and return an :class:`AgentResult`."""
        raise NotImplementedError

    # ------------------------------------------------------------------ #
    # Shared helpers
    # ------------------------------------------------------------------ #
    def escalate(self, task: Task, reason: str) -> AgentResult:
        """Pass a decision up the chain (to ``reports_to`` and ultimately the owner)."""
        target = self.reports_to or "owner"
        self.log.info("Escalating '%s' to %s: %s", task.name, target, reason)
        return AgentResult(self.name, STATUS_ESCALATED, f"escalated to {target}: {reason}")

    def block_for_approval(self, action: str) -> AgentResult:
        """Refuse an action that requires explicit human approval (e.g. publishing)."""
        self.log.info("Blocked '%s': requires human approval before proceeding.", action)
        return AgentResult(
            self.name, STATUS_BLOCKED, f"'{action}' requires human approval before proceeding."
        )

    def not_implemented(self, what: str) -> AgentResult:
        """Standard skeleton response for unbuilt behaviour."""
        self.log.debug("Skeleton: '%s' not implemented yet.", what)
        return AgentResult(self.name, STATUS_NOT_IMPLEMENTED, f"{what} not implemented (Phase 1 skeleton).")

    def describe(self) -> dict[str, Any]:
        """Machine-readable summary of this agent (used by Hermes / status banners)."""
        return {
            "name": self.name,
            "role": self.role,
            "reports_to": self.reports_to,
            "can_publish_directly": self.can_publish_directly,
        }
