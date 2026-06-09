"""Gated automation rules.

Content may move toward ``approved_for_scheduled_publish`` ONLY after all six gates pass:

    Gate 1: Draft created
    Gate 2: Sentinel review passed
    Gate 3: Platform Compliance review passed (risk below threshold)
    Gate 4: Owner approval received
    Gate 5: Publish/schedule permission confirmed
    Gate 6: Final preflight check passed

Even when all gates pass, this only sets ``approved_for_scheduled_publish`` — it never
publishes. Actual publishing is a future, separately-approved phase.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from review.models import (
    GATE_COMPLIANCE,
    GATE_DRAFT_CREATED,
    GATE_OWNER_APPROVAL,
    GATE_PREFLIGHT,
    GATE_SCHEDULE_PERMISSION,
    GATE_SENTINEL,
    STATUS_REJECTED,
    ReviewItem,
)


@dataclass
class GateResult:
    name: str
    passed: bool
    detail: str = ""


@dataclass
class GateReport:
    results: list[GateResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(r.passed for r in self.results)

    @property
    def failing(self) -> list[str]:
        return [r.name for r in self.results if not r.passed]

    def as_dict(self) -> dict:
        return {r.name: {"passed": r.passed, "detail": r.detail} for r in self.results}


def preflight(item: ReviewItem) -> tuple[bool, str]:
    """Gate 6: last automated sanity check before scheduling."""
    if item.published:
        return False, "item is already marked published (must not be)"
    if item.status == STATUS_REJECTED:
        return False, "item was rejected"
    if not (item.content or "").strip():
        return False, "draft content is empty"
    if not item.skill:
        return False, "missing skill reference"
    return True, "preflight ok"


def evaluate_scheduling_gates(item: ReviewItem, *, owner_authorizing: bool) -> GateReport:
    """Evaluate all six gates for scheduled-publish approval.

    ``owner_authorizing`` is True only when the owner is actively performing the
    "approve for scheduled publishing" action — it supplies Gate 4 and Gate 5. The other
    gates are read from the item's recorded pipeline state and a fresh preflight check.
    """
    results: list[GateResult] = []
    g = item.gates or {}

    results.append(GateResult(GATE_DRAFT_CREATED, bool(g.get(GATE_DRAFT_CREATED)), "draft exists"))
    results.append(GateResult(GATE_SENTINEL, bool(g.get(GATE_SENTINEL)), "sentinel reviewed skill permissions"))
    comp_passed = bool(item.compliance.get("passed"))
    results.append(GateResult(GATE_COMPLIANCE, comp_passed, f"risk_score={item.compliance.get('risk_score')}"))
    results.append(GateResult(GATE_OWNER_APPROVAL, bool(owner_authorizing), "owner approval received"))
    results.append(GateResult(GATE_SCHEDULE_PERMISSION, bool(owner_authorizing), "owner granted scheduling permission"))
    ok6, detail6 = preflight(item)
    results.append(GateResult(GATE_PREFLIGHT, ok6, detail6))

    return GateReport(results)
