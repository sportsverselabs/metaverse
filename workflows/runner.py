"""Workflow runner (skeleton).

Runs an ordered list of steps, each delegating to a registered agent. The key Phase 1
feature is the **human-approval gate**: any step flagged ``requires_approval`` halts the
workflow with a ``blocked`` result unless approval was explicitly granted. This enforces
"human approval required before public posting" at the workflow level.

Phase 1 status: SKELETON wiring — it executes steps by calling ``agent.handle(...)`` and
respects the approval gate, but no production workflows are defined yet.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from agents.base import AgentResult, BaseAgent, STATUS_BLOCKED, Task
from core.logging_setup import get_logger


@dataclass
class Step:
    name: str
    agent: str                       # name of the agent to handle this step
    task: str                        # task name passed to that agent
    requires_approval: bool = False  # True for anything public-facing / irreversible
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass
class Workflow:
    name: str
    steps: list[Step] = field(default_factory=list)


class WorkflowRunner:
    def __init__(self, agents: dict[str, BaseAgent], logger=None) -> None:
        self.agents = agents
        self.log = logger or get_logger("workflow")

    def run(self, workflow: Workflow, *, approvals: set[str] | None = None) -> list[AgentResult]:
        """Execute a workflow step by step.

        ``approvals`` is the set of step names a human has explicitly approved. A step
        that ``requires_approval`` but is not in this set is BLOCKED and stops the run.
        """
        approvals = approvals or set()
        results: list[AgentResult] = []
        self.log.info("Running workflow '%s' (%d steps)", workflow.name, len(workflow.steps))

        for step in workflow.steps:
            if step.requires_approval and step.name not in approvals:
                self.log.info("Step '%s' BLOCKED: needs human approval.", step.name)
                results.append(
                    AgentResult("workflow", STATUS_BLOCKED,
                                f"step '{step.name}' requires human approval before running")
                )
                break  # stop the workflow at the gate

            agent = self.agents.get(step.agent)
            if agent is None:
                results.append(
                    AgentResult("workflow", STATUS_BLOCKED, f"no agent '{step.agent}' for step '{step.name}'")
                )
                break

            result = agent.handle(Task(name=step.task, payload=step.payload, requested_by="workflow"))
            self.log.info("Step '%s' -> %s (%s)", step.name, result.status, result.detail)
            results.append(result)

        return results
