"""Sportsverse OS — agents package.

Chain of command (see ../architecture/agent_architecture.md):

    Owner (human)
     └─ Hermes        CEO / orchestrator
         ├─ OpenClaw  skill-execution layer (UNDER Hermes)
         ├─ Sentinel  integrity / security / drift monitor
         ├─ Archivist institutional memory & handoff keeper
         └─ Compliance compliance division (platform/copyright/FTC/brand safety)

Phase 1 status: SKELETONS. Each agent defines its role, permissions, and method
surface, but real behaviour is stubbed. Hard safety rules are enforced even in the
skeleton: no public posting and no template-free DM/comment replies without explicit
human approval.
"""

from agents.base import AgentResult, BaseAgent, Task  # noqa: F401

__all__ = ["BaseAgent", "Task", "AgentResult"]
