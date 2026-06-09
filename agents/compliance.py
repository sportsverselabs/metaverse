"""Compliance Division.

Reviews content before anything is marked ready for owner review / scheduling. Covers the
owner's dimensions: platform policy, copyright, fair use, affiliate, FTC disclosure, brand
safety, and per-platform review (YouTube / TikTok / Instagram).

Each dimension now runs a real (deterministic, offline) heuristic returning ``pass`` / ``warn`` /
``flag`` with notes, plus a 0–100 risk score. ``passed`` (Gate 3) is True only when the risk is
below threshold AND no critical dimension (platform policy / copyright) is flagged. Nothing is
EVER auto-approved — the verdict is always ``needs_human_review`` and a human decides.

(An optional LLM-assisted second opinion can be layered on later via :meth:`llm_assist`; it is
intentionally not called by default to keep reviews deterministic and free.)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from agents.base import AgentResult, BaseAgent, STATUS_BLOCKED, Task
from core.policy import COMPLIANCE_RISK_THRESHOLD

CHECKS = [
    "platform_policy", "copyright", "fair_use", "affiliate_disclosure", "ftc_disclosure",
    "brand_safety", "youtube_review", "tiktok_review", "instagram_review",
]
CRITICAL_CHECKS = ("platform_policy", "copyright")  # a flag here blocks Gate 3 outright

VERDICT_NEEDS_HUMAN = "needs_human_review"
VERDICT_APPROVED = "approved"
VERDICT_REJECTED = "rejected"

STATUS_PASS, STATUS_WARN, STATUS_FLAG = "pass", "warn", "flag"

# Heuristic signal sets (lowercase substring match). Deterministic and offline.
RISKY_TERMS = {
    "guarantee": 15, "guaranteed": 15, "100%": 10, "get rich": 20, "make money fast": 20,
    "free money": 20, "miracle": 12, "cure": 15, "click here": 8, "limited time": 5,
}
AFFILIATE_HINTS = ("affiliate", "discount code", "promo code", "commission", "buy now", "shop now")
DISCLOSURE_HINTS = ("#ad", "sponsored", "disclosure", "paid partnership", "affiliate link")
POLICY_HINTS = ("hate", "violence", "kill ", "slur", "graphic", "nsfw", "explicit")
COPYRIGHT_HINTS = ("official footage", "broadcast footage", "full match", "copyrighted",
                   "all rights reserved", "©", "espn", "sky sports", "nba tv", "broadcast clip")
FAIRUSE_POS = ("commentary", "analysis", "review", "reaction", "educational", "transformative", "highlights")
MUSIC_HINTS = ("song", "music", "soundtrack", "audio track", "copyrighted music", "trending sound")
PROFANITY = ("damn", "hell ", "crap", "wtf")
GAMBLING = ("betting", "gambling", "odds", "parlay", "sportsbook")


@dataclass
class ComplianceResult:
    approved: bool
    verdict: str
    risk_score: int = 0
    passed: bool = False                       # Gate 3: risk acceptable + no critical flag
    checks: dict[str, str] = field(default_factory=dict)
    notes: str = ""


class Compliance(BaseAgent):
    name = "compliance"
    role = "Compliance Division"
    reports_to = "hermes"

    # ------------------------------------------------------------------ #
    def _run_checks(self, content: str) -> tuple[dict[str, str], list[str], int]:
        t = (content or "").lower()
        checks: dict[str, str] = {}
        notes: list[str] = []
        score = 0

        for term, weight in RISKY_TERMS.items():
            if term in t:
                score += weight
                notes.append(f"risky term '{term}'")

        # platform_policy (critical)
        if any(k in t for k in POLICY_HINTS):
            checks["platform_policy"] = STATUS_FLAG
            score += 25
            notes.append("possible platform-policy violation (violence/hate/explicit)")
        else:
            checks["platform_policy"] = STATUS_PASS

        # copyright (critical)
        if any(k in t for k in COPYRIGHT_HINTS):
            checks["copyright"] = STATUS_FLAG
            score += 25
            notes.append("possible copyrighted/broadcast material")
        else:
            checks["copyright"] = STATUS_PASS

        # fair_use
        if checks["copyright"] == STATUS_FLAG and not any(k in t for k in FAIRUSE_POS):
            checks["fair_use"] = STATUS_WARN
            score += 10
            notes.append("no clear transformative/fair-use signal")
        else:
            checks["fair_use"] = STATUS_PASS

        # affiliate_disclosure
        if any(h in t for h in AFFILIATE_HINTS) and not any(d in t for d in DISCLOSURE_HINTS):
            checks["affiliate_disclosure"] = STATUS_FLAG
            score += 20
            notes.append("affiliate/monetisation language without a disclosure")
        else:
            checks["affiliate_disclosure"] = STATUS_PASS

        # ftc_disclosure (follows affiliate)
        if checks["affiliate_disclosure"] == STATUS_FLAG:
            checks["ftc_disclosure"] = STATUS_FLAG
            notes.append("FTC disclosure likely required")
        else:
            checks["ftc_disclosure"] = STATUS_PASS

        # brand_safety
        if any(k in t for k in POLICY_HINTS) or any(p in t for p in PROFANITY) or any(g in t for g in GAMBLING):
            checks["brand_safety"] = STATUS_WARN
            score += 8
            notes.append("brand-safety language (profanity/gambling/controversial)")
        else:
            checks["brand_safety"] = STATUS_PASS

        # per-platform review (music/copyright is the usual short-form trigger)
        music_or_copy = checks["copyright"] == STATUS_FLAG or any(k in t for k in MUSIC_HINTS)
        platform_status = STATUS_WARN if music_or_copy else STATUS_PASS
        checks["youtube_review"] = platform_status
        checks["tiktok_review"] = platform_status
        checks["instagram_review"] = platform_status
        if music_or_copy:
            notes.append("per-platform music/copyright review advised (YT/TikTok/IG)")

        return checks, notes, max(0, min(100, score))

    def review_draft(self, content: str, platform: Optional[str] = None) -> ComplianceResult:
        """Run all dimension checks. Never auto-approves; a human always decides.

        Gate 3 (``passed``) requires risk below threshold AND no dimension ``flag`` (a real
        problem like copyright or a missing disclosure). ``warn`` is advisory and does not block.
        """
        checks, notes, score = self._run_checks(content or "")
        any_flag = any(v == STATUS_FLAG for v in checks.values())
        passed = (score < COMPLIANCE_RISK_THRESHOLD) and not any_flag
        self.log.info("Compliance review: platform=%s risk=%d passed=%s flags=%s",
                      platform, score, passed,
                      [k for k, v in checks.items() if v == STATUS_FLAG])
        return ComplianceResult(
            approved=False,
            verdict=VERDICT_NEEDS_HUMAN,
            risk_score=score,
            passed=passed,
            checks=checks,
            notes="; ".join(notes) if notes else "no automated flags (still requires human approval)",
        )

    # Backwards-compatible alias (Phase 1).
    def review(self, content: str, platform: Optional[str] = None) -> ComplianceResult:
        return self.review_draft(content, platform)

    def llm_assist(self, content: str, llm) -> Optional[str]:
        """OPTIONAL hook for a model-assisted second opinion. Not called by default."""
        if llm is None:
            return None
        resp = llm.complete(
            f"Act as a strict social-media compliance reviewer. List concrete risks (copyright, "
            f"fair use, FTC/affiliate disclosure, platform policy, brand safety) for this DRAFT. "
            f"Do not approve it.\n\nDRAFT:\n{content}",
            task_type="compliance",
        )
        return getattr(resp, "text", None)

    def handle(self, task: Task) -> AgentResult:
        if task.name in {"review", "review_content", "review_draft"}:
            result = self.review_draft(task.payload.get("content", ""), task.payload.get("platform"))
            return AgentResult(
                self.name,
                STATUS_BLOCKED,  # never clears for auto-publishing
                detail=f"verdict={result.verdict} risk={result.risk_score} passed={result.passed} (human approval required)",
                data={
                    "approved": result.approved, "verdict": result.verdict,
                    "risk_score": result.risk_score, "passed": result.passed,
                    "checks": result.checks, "notes": result.notes,
                },
            )
        return self.not_implemented(f"compliance task '{task.name}'")
