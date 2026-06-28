"""Graph nodes + routing logic for the Hermes operating core.

Node functions are shared between the LangGraph engine (when installed) and the built-in
fallback runner. Each node takes ``(state, ctx)`` and returns the (mutated) state, recording its
name in ``state.path``.

Flow:
    jarvis_input -> hermes_router -> cost_router
        -> [if cost gate tripped] human_approval_gate -> memory_logger -> final_report
        -> [else] <worker> -> compliance_agent -> human_approval_gate
                 -> execution_agent -> memory_logger -> final_report

Safety: ``execution_agent`` performs NO production actions. Anything gated (publish/send/spend/
install/server/payment) becomes a pending approval request; nothing happens automatically.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from core.logging_setup import get_logger

# The 13 nodes of the orchestration graph (per the Phase 4 spec).
NODE_NAMES = [
    "jarvis_input", "hermes_router", "cost_router", "research_agent", "coding_agent",
    "content_agent", "compliance_agent", "openclaw_skill_agent", "nemotron_reasoning_agent",
    "human_approval_gate", "execution_agent", "memory_logger", "final_report",
]

WORKER_ROUTES = {"research_agent", "content_agent", "coding_agent", "nemotron_reasoning_agent", "openclaw_skill_agent"}

# Routes whose output is publishable content that should flow into the owner-review queue
# (draft -> review -> schedule). Internal-only outputs (research/coding) are not auto-queued.
SUBMIT_TO_REVIEW_ROUTES = {"content_agent"}

_log = get_logger("orchestration")


@dataclass
class GraphContext:
    jarvis: Any
    hermes: Any
    model_router: Any
    workers: dict                      # route name -> worker object with .run(state)
    compliance_agent: Any
    approval_queue: Any
    journal: Any
    memory: Any = None
    review_store: Any = None           # optional: queue content drafts into the review surface
    extras: dict = field(default_factory=dict)


# --------------------------------------------------------------------------- #
# Nodes
# --------------------------------------------------------------------------- #
def node_jarvis_input(state, ctx: GraphContext):
    state.visit("jarvis_input")
    parsed = ctx.jarvis.parse(state.user_request, state.source)
    state.task_type = parsed["task_type"]
    state.complexity = parsed["complexity"]
    state.risk = parsed["risk"]
    state.gated_actions = parsed.get("gated_actions", [])
    state.requested_skill = parsed.get("requested_skill", "")
    # Ground drafting requests with real-time sports data (best-effort; never breaks the flow).
    sc = ctx.extras.get("sports_context") if ctx.extras else None
    if sc is not None and not state.gated_actions:
        try:
            state.sports_brief = sc.brief(state.user_request)
        except Exception:
            state.sports_brief = ""
    return state


def node_hermes_router(state, ctx: GraphContext):
    state.visit("hermes_router")
    ctx.hermes.decide(state)   # Hermes sets route + flags gated actions
    return state


def node_cost_router(state, ctx: GraphContext):
    state.visit("cost_router")
    mr = ctx.model_router
    provider, model = mr.select(state.task_type, state.complexity)
    est_tokens = mr.estimate_tokens(state.user_request, None)
    est_cost = mr.estimate_cost(provider, est_tokens)
    state.model_provider, state.model_name = provider, model
    state.est_tokens, state.est_cost = est_tokens, est_cost

    threshold = float(mr.budget.get("per_task_approval_threshold_usd", 0.5))
    monthly = float(mr.budget.get("monthly_budget_usd", 0.0))
    over_task = est_cost > threshold
    over_month = monthly > 0 and (mr.cost_tracker.month_total() + est_cost) > monthly
    if over_task or over_month:
        state.needs_approval = True
        state.approval_kind = "cost"
        if over_task:
            state.approval_reasons.append(f"estimated ${est_cost:.4f} exceeds per-task threshold ${threshold:.2f}")
        if over_month:
            state.approval_reasons.append("would exceed monthly budget")
    return state


def node_worker(state, ctx: GraphContext):
    worker = ctx.workers.get(state.route)
    if worker is None:
        return state  # e.g. compliance route -> handled by the compliance node
    state.visit(state.route)
    worker.run(state)
    return state


def node_compliance(state, ctx: GraphContext):
    state.visit("compliance_agent")
    ctx.compliance_agent.run(state)
    return state


def node_human_approval_gate(state, ctx: GraphContext):
    state.visit("human_approval_gate")

    # A blocked unapproved skill is already stopped — no approval request needed.
    if state.final_status == "blocked_unapproved_skill":
        state.approval_status = "not_required"
        return state

    cost_gated = state.needs_approval and state.approval_kind == "cost"
    action_gated = bool(state.gated_actions)
    compliance_failed = bool(state.compliance) and not state.compliance.get("passed", True)

    if cost_gated or action_gated or compliance_failed:
        state.needs_approval = True
        if action_gated:
            action = state.gated_actions[0]
        elif cost_gated:
            action = "spend_over_threshold"
        else:
            action = "publish_content"  # compliance-failed content needs explicit human sign-off
        reason = "; ".join(state.approval_reasons) or f"gated action: {action}"
        req = ctx.approval_queue.request(action, reason, task_id=state.task_id,
                                         details={"route": state.route, "est_cost": state.est_cost})
        state.approval_id = req.id
        state.approval_status = "pending"
        _log.info("Approval required for task %s (%s).", state.task_id, action)
    else:
        state.approval_status = "not_required"
    return state


def node_execution_agent(state, ctx: GraphContext):
    state.visit("execution_agent")
    # SAFETY INVARIANT: this node NEVER publishes, sends, spends, installs, or changes
    # production state. Its ONLY "action" is the safe, internal step of queuing a
    # compliance-passing content draft into the owner-review surface (draft -> review ->
    # schedule). Real production actions are a future, separately-approved capability.
    if state.approval_status == "pending":
        state.final_status = "pending_approval"
        return state
    if state.final_status == "blocked_unapproved_skill":
        return state
    if _maybe_submit_to_review(state, ctx):
        state.final_status = "submitted_to_review"
    else:
        state.final_status = state.final_status or "completed_no_external_action"
    return state


def _maybe_submit_to_review(state, ctx: GraphContext) -> bool:
    """Queue a publishable, compliance-passing content draft into the review surface. Internal only."""
    if ctx.review_store is None or state.route not in SUBMIT_TO_REVIEW_ROUTES:
        return False
    if not (state.output or "").strip():
        return False
    comp = state.compliance or {}
    if not comp.get("passed", False):
        return False  # only queue drafts that passed compliance; others wait for revision
    try:
        from review.models import make_review_item
        item = make_review_item(
            skill=state.route,
            content=state.output,
            risk_score=int(comp.get("risk_score", 0)),
            compliance={"verdict": comp.get("verdict"), "risk_score": comp.get("risk_score"),
                        "passed": comp.get("passed"), "notes": comp.get("notes")},
            source_text=state.user_request,
            sentinel_passed=True,
            compliance_passed=bool(comp.get("passed")),
        )
        ctx.review_store.add(item)
        state.review_id = item.id
        _log.info("Queued content draft %s into the owner-review surface.", item.id)
        return True
    except Exception:
        _log.debug("review submission failed", exc_info=True)
        return False


def node_memory_logger(state, ctx: GraphContext):
    state.visit("memory_logger")
    try:
        ctx.journal.append(state.to_journal_record())
    except Exception:
        _log.debug("journal append failed", exc_info=True)
    if ctx.memory is not None and hasattr(ctx.memory, "log_audit"):
        try:
            ctx.memory.log_audit(
                draft_id=state.task_id, action="orchestrated_task", agent="hermes",
                owner_decision=state.approval_status,
                compliance_score=(state.compliance.get("risk_score") if state.compliance else None),
                final_status=state.final_status,
            )
        except Exception:
            _log.debug("audit log failed", exc_info=True)
    return state


def node_final_report(state, ctx: GraphContext):
    state.visit("final_report")
    ctx.jarvis.report(state)
    return state


# --------------------------------------------------------------------------- #
# Built-in fallback runner (used when LangGraph isn't installed; same node flow)
# --------------------------------------------------------------------------- #
def run_fallback(state, ctx: GraphContext):
    node_jarvis_input(state, ctx)
    node_hermes_router(state, ctx)
    node_cost_router(state, ctx)

    if state.needs_approval and state.approval_kind == "cost":
        # Do NOT spend on the model — route straight to the approval gate.
        node_human_approval_gate(state, ctx)
        node_memory_logger(state, ctx)
        node_final_report(state, ctx)
        return state

    node_worker(state, ctx)
    node_compliance(state, ctx)
    node_human_approval_gate(state, ctx)
    node_execution_agent(state, ctx)
    node_memory_logger(state, ctx)
    node_final_report(state, ctx)
    return state


def bind(node: Callable, ctx: GraphContext) -> Callable:
    """Wrap a (state, ctx) node into a (state) callable for LangGraph."""
    def _wrapped(state):
        return node(state, ctx)
    return _wrapped
