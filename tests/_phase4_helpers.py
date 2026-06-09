"""Shared helpers for Phase 4 tests (not collected as tests)."""

from __future__ import annotations

from agents.coding_agent import CodingAgent
from agents.compliance_agent import ComplianceAgent
from agents.content_agent import ContentAgent
from agents.hermes import Hermes
from agents.jarvis import Jarvis
from agents.nemotron_reasoning_agent import NemotronReasoningAgent
from agents.openclaw_skill_agent import OpenClawSkillAgent
from agents.research_agent import ResearchAgent
from approval.approval_queue import ApprovalQueue
from memory.manager import MemoryManager
from orchestration.journal import AgentJournal
from orchestration.routes import GraphContext
from providers.model_router import CostTracker, ModelRouter


def make_ctx(tmp_path, *, budget=None, review_store=None):
    """A fully wired GraphContext in MOCK mode (no network, no spend) with temp dirs.

    ``review_store`` is None by default (no auto-queueing) so existing tests stay deterministic.
    Pass a ReviewStore to exercise the orchestration -> review-queue wiring.
    """
    memory = MemoryManager(store_dir=tmp_path / "mem")
    model_router = ModelRouter(config=None, budget=budget,
                               cost_tracker=CostTracker(tmp_path / "ledger.json"))
    workers = {
        "research_agent": ResearchAgent(model_router),
        "content_agent": ContentAgent(model_router),
        "coding_agent": CodingAgent(model_router),
        "nemotron_reasoning_agent": NemotronReasoningAgent(model_router),
        "openclaw_skill_agent": OpenClawSkillAgent(memory=memory),
    }
    return GraphContext(
        jarvis=Jarvis(),
        hermes=Hermes(memory=memory),
        model_router=model_router,
        workers=workers,
        compliance_agent=ComplianceAgent(),
        approval_queue=ApprovalQueue(base_dir=tmp_path / "approvals", memory=memory),
        journal=AgentJournal(path=tmp_path / "journal.jsonl"),
        memory=memory,
        review_store=review_store,
    )
