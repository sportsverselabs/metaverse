"""Central safety policy constants.

Single source of truth for what skills/agents may never do, and which risk levels are
blocked by default. Imported by Sentinel, the skill registry, OpenClaw, and Compliance so
the rules can't drift apart. Derived from constitution/constitution.md.
"""

from __future__ import annotations

# Risk levels
RISK_LOW = "low"
RISK_MEDIUM = "medium"
RISK_HIGH = "high"
RISK_LEVELS = (RISK_LOW, RISK_MEDIUM, RISK_HIGH)

# Risk levels that Sentinel blocks unless the owner explicitly overrides.
BLOCKED_RISK_LEVELS = frozenset({RISK_HIGH})

# Compliance gate threshold: a draft whose risk score is BELOW this is considered to have
# "passed" the automated compliance check (Gate 3). At/above it, scheduling is blocked until
# the draft is revised. A human must still approve regardless (Gate 4) — passing this gate is
# necessary, not sufficient.
COMPLIANCE_RISK_THRESHOLD = 50

# Actions NO draft-only skill may ever perform. If a skill's `allowed_actions` intersects
# this set, the registry refuses to register it and Sentinel blocks it.
FORBIDDEN_ACTIONS = frozenset({
    "publish",
    "post",
    "social_post",
    "upload",
    "email_external",
    "send_email_external",
    "send_dm_freetext",
    "purchase",
    "buy",
    "spend_money",
    "sign_contract",
    "modify_production_code",
    "deploy",
    "delete_data",
})

# Actions that are safe for draft-only skills.
SAFE_DRAFT_ACTIONS = frozenset({
    "create_draft",
    "write_report",
    "summarize",
    "research_public_info",
    "assess_content",
    "outline",
})
