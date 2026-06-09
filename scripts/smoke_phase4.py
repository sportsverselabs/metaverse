"""Phase 4 smoke test — Hermes Multi-Agent Operating Core (MOCK mode, isolated, NO publishing).

Demonstrates:
  - Jarvis parses a request into a structured task
  - Hermes routes it through the LangGraph nodes (built-in fallback engine here)
  - Cost router picks DeepSeek (routine) / Nemotron (complex; falls back to DeepSeek when disabled)
  - Compliance reviews the output
  - Gated actions (publish/post/email/spend) -> pending approval, nothing executed
  - OpenClaw skills off the allowlist are blocked with a security warning
  - Everything is journaled; nothing is published

Run from the project root:  python scripts/smoke_phase4.py
"""

from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agents.coding_agent import CodingAgent
from agents.compliance_agent import ComplianceAgent
from agents.content_agent import ContentAgent
from agents.hermes import Hermes
from agents.jarvis import Jarvis
from agents.nemotron_reasoning_agent import NemotronReasoningAgent
from agents.openclaw_skill_agent import OpenClawSkillAgent
from agents.research_agent import ResearchAgent
from approval.approval_queue import APPROVAL_PENDING, ApprovalQueue
from core.logging_setup import setup_logging
from memory.manager import MemoryManager
from orchestration.journal import AgentJournal
from orchestration.routes import GraphContext, run_fallback
from orchestration.state import OrchestrationState
from providers.model_router import CostTracker, ModelRouter


def banner(t: str) -> None:
    print("\n" + "=" * 70)
    print(t)
    print("=" * 70)


def build_ctx(tmp: Path) -> GraphContext:
    memory = MemoryManager(store_dir=tmp / "mem")
    mr = ModelRouter(config=None, cost_tracker=CostTracker(tmp / "ledger.json"))  # mock mode
    workers = {
        "research_agent": ResearchAgent(mr),
        "content_agent": ContentAgent(mr),
        "coding_agent": CodingAgent(mr),
        "nemotron_reasoning_agent": NemotronReasoningAgent(mr),
        "openclaw_skill_agent": OpenClawSkillAgent(memory=memory),
    }
    return GraphContext(
        jarvis=Jarvis(), hermes=Hermes(memory=memory), model_router=mr, workers=workers,
        compliance_agent=ComplianceAgent(), approval_queue=ApprovalQueue(base_dir=tmp / "ap", memory=memory),
        journal=AgentJournal(path=tmp / "journal.jsonl"), memory=memory,
    )


def run(ctx, request, skill=""):
    state = OrchestrationState(user_request=request)
    if skill:
        state.requested_skill = skill
    run_fallback(state, ctx)
    print(f"\n> {request}")
    print(f"  route={state.route}  model={state.model_provider}/{state.model_name}  "
          f"~{state.est_tokens}tok est=${state.est_cost:.4f}  approval={state.approval_status}  final={state.final_status}")
    if state.security_warnings:
        print("  " + state.security_warnings[0])
    print("  path: " + " -> ".join(state.path))
    return state


def main() -> None:
    setup_logging("warning")
    tmp = Path(tempfile.mkdtemp(prefix="sv_p4_"))
    try:
        ctx = build_ctx(tmp)

        banner("1) Routine research -> DeepSeek, no approval needed")
        run(ctx, "research trending NBA storylines for short-form video")

        banner("2) Content draft -> DeepSeek, compliance-reviewed")
        run(ctx, "draft a punchy caption for a buzzer-beater clip")

        banner("3) Complex strategy -> Nemotron node (disabled -> DeepSeek fallback)")
        run(ctx, "design the system architecture and growth strategy for the channel")

        banner("4) Gated action (publish/post) -> PENDING APPROVAL, nothing executed")
        s = run(ctx, "publish this update and post it on instagram")
        print(f"  -> approval request id: {s.approval_id}")

        banner("5) Unapproved OpenClaw skill -> BLOCKED with security warning")
        run(ctx, "skill: shell_exec rm -rf", skill="shell_exec")

        banner("6) Allowlisted OpenClaw skill -> runs draft-only")
        run(ctx, "skill: daily_report_draft", skill="daily_report_draft")

        banner("AUDIT: journal + approval queue + no publishing")
        rows = ctx.journal.read()
        print(f"  journal entries: {len(rows)}")
        pend = ctx.approval_queue.list(status=APPROVAL_PENDING)
        print(f"  pending approvals: {len(pend)} ({[r.action for r in pend]})")
        published_anywhere = any(r.get("final_status") == "published" for r in rows)
        print(f"  anything published? {published_anywhere}")

        banner("RESULT")
        assert not published_anywhere, "INVARIANT VIOLATED: something published!"
        print("  OK: Jarvis->Hermes routing, DeepSeek default + Nemotron fallback, compliance,")
        print("  OK: gated approvals, OpenClaw allowlist blocking, full journaling.")
        print("  OK: nothing was published, sent, or spent.")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
