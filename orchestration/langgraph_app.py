"""LangGraph orchestration app.

Builds the stateful agent graph. If the ``langgraph`` package is installed, a real compiled
``StateGraph`` is used; otherwise an equivalent built-in runner executes the SAME node functions
in the same order. Either way the behaviour and safety gates are identical, so the system runs
and is fully testable with zero extra dependencies. (`pip install langgraph` to use the real engine.)
"""

from __future__ import annotations

import dataclasses
from typing import Optional

from agents.coding_agent import CodingAgent
from agents.compliance_agent import ComplianceAgent
from agents.content_agent import ContentAgent
from agents.hermes import Hermes
from agents.jarvis import Jarvis
from agents.nemotron_reasoning_agent import NemotronReasoningAgent
from agents.openclaw_skill_agent import OpenClawSkillAgent
from agents.research_agent import ResearchAgent
from approval.approval_queue import ApprovalQueue
from core.config import load_config
from core.logging_setup import get_logger, setup_logging
from memory.manager import MemoryManager
from orchestration import routes
from orchestration.journal import AgentJournal
from orchestration.routes import GraphContext, bind, run_fallback
from orchestration.state import OrchestrationState
from providers.model_router import ModelRouter
from review.store import ReviewStore

_log = get_logger("orchestration.app")


def build_services(config=None, *, memory=None) -> GraphContext:
    """Assemble all Phase 4 services into a GraphContext. Reuses live config/.env."""
    config = config or load_config()
    setup_logging(config.log_level)
    memory = memory or MemoryManager()
    model_router = ModelRouter(config=config)
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
        approval_queue=ApprovalQueue(memory=memory),
        journal=AgentJournal(),
        memory=memory,
        review_store=ReviewStore(),   # content drafts flow into `python -m review`
    )


def langgraph_available() -> bool:
    try:
        import langgraph  # noqa: F401
        return True
    except Exception:
        return False


def build_langgraph_app(ctx: GraphContext):
    """Build a compiled LangGraph StateGraph mirroring the fallback flow. Returns None on failure."""
    try:
        from langgraph.graph import END, StateGraph

        def worker_node(route_name):
            def _n(state, _ctx=ctx, _r=route_name):
                state.visit(_r)
                w = _ctx.workers.get(_r)
                if w:
                    w.run(state)
                return state
            return _n

        g = StateGraph(OrchestrationState)
        g.add_node("jarvis_input", bind(routes.node_jarvis_input, ctx))
        g.add_node("hermes_router", bind(routes.node_hermes_router, ctx))
        g.add_node("cost_router", bind(routes.node_cost_router, ctx))
        for name in ("research_agent", "content_agent", "coding_agent",
                     "nemotron_reasoning_agent", "openclaw_skill_agent"):
            g.add_node(name, worker_node(name))
        g.add_node("compliance_agent", bind(routes.node_compliance, ctx))
        g.add_node("human_approval_gate", bind(routes.node_human_approval_gate, ctx))
        g.add_node("execution_agent", bind(routes.node_execution_agent, ctx))
        g.add_node("memory_logger", bind(routes.node_memory_logger, ctx))
        g.add_node("final_report", bind(routes.node_final_report, ctx))

        g.set_entry_point("jarvis_input")
        g.add_edge("jarvis_input", "hermes_router")
        g.add_edge("hermes_router", "cost_router")

        def after_cost(state):
            if state.needs_approval and state.approval_kind == "cost":
                return "human_approval_gate"
            return state.route or "research_agent"

        g.add_conditional_edges("cost_router", after_cost, {
            "human_approval_gate": "human_approval_gate",
            "research_agent": "research_agent", "content_agent": "content_agent",
            "coding_agent": "coding_agent", "nemotron_reasoning_agent": "nemotron_reasoning_agent",
            "openclaw_skill_agent": "openclaw_skill_agent", "compliance_agent": "compliance_agent",
        })
        for name in ("research_agent", "content_agent", "coding_agent",
                     "nemotron_reasoning_agent", "openclaw_skill_agent"):
            g.add_edge(name, "compliance_agent")
        g.add_edge("compliance_agent", "human_approval_gate")

        def after_gate(state):
            return "memory_logger" if state.approval_status == "pending" else "execution_agent"

        g.add_conditional_edges("human_approval_gate", after_gate,
                                {"memory_logger": "memory_logger", "execution_agent": "execution_agent"})
        g.add_edge("execution_agent", "memory_logger")
        g.add_edge("memory_logger", "final_report")
        g.add_edge("final_report", END)
        return g.compile()
    except Exception:
        _log.warning("Could not build LangGraph app; using fallback runner.", exc_info=True)
        return None


def _coerce_state(result) -> Optional[OrchestrationState]:
    if isinstance(result, OrchestrationState):
        return result
    if isinstance(result, dict):
        names = {f.name for f in dataclasses.fields(OrchestrationState)}
        return OrchestrationState(**{k: v for k, v in result.items() if k in names})
    return None


def run_task(user_request: str, source: str = "cli", ctx: Optional[GraphContext] = None) -> OrchestrationState:
    """Run one task through the graph. Uses LangGraph if installed, else the built-in runner."""
    ctx = ctx or build_services()
    state = OrchestrationState(user_request=user_request, source=source)

    if langgraph_available():
        app = build_langgraph_app(ctx)
        if app is not None:
            try:
                coerced = _coerce_state(app.invoke(state))
                if coerced is not None:
                    return coerced
            except Exception:
                _log.warning("LangGraph invoke failed; using fallback runner.", exc_info=True)
    return run_fallback(state, ctx)


def engine_name() -> str:
    return "langgraph" if langgraph_available() else "builtin-fallback"
