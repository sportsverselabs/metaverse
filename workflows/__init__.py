"""Sportsverse OS — workflows package.

Multi-step automations that coordinate agents. Phase 1 ships the runner skeleton plus
the data types for describing a workflow. Steps marked ``requires_approval`` (e.g.
anything that publishes) are gated: the runner stops and reports rather than proceeding
without explicit human approval.
"""

from workflows.runner import Step, Workflow, WorkflowRunner  # noqa: F401

__all__ = ["Step", "Workflow", "WorkflowRunner"]
