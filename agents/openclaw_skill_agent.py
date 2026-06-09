"""OpenClaw skill agent — a CONTROLLED skill adapter (not an orchestrator).

OpenClaw is never the main orchestrator; Hermes routes to it only when a skill is requested.
This adapter enforces an allowlist (``config/openclaw_allowlist.json``): every skill not
explicitly ``allowed: true`` is BLOCKED by default. Allowed skills run via the Phase 2
draft-only registry. Skills may never use forbidden capabilities (secrets, api_keys, shell,
production_database, payments, publish, ...). Every invocation is logged; unknown skills raise a
security warning.
"""

from __future__ import annotations

import json
from typing import Any, Optional

from agents.base import Task
from agents.openclaw import OpenClaw
from core import paths
from core.logging_setup import get_logger
from skills.registry import default_registry


class OpenClawSkillAgent:
    name = "openclaw_skill_agent"

    def __init__(self, allowlist_path=None, openclaw: Optional[OpenClaw] = None, memory=None, logger=None) -> None:
        self.log = logger or get_logger("agent.openclaw_skill")
        self.allowlist_path = allowlist_path or paths.OPENCLAW_ALLOWLIST_FILE
        self.memory = memory
        self._allowlist = self._load_allowlist()
        # Real execution still goes through the draft-only registry.
        self.openclaw = openclaw or OpenClaw(registry=default_registry(), logger=self.log)

    def _load_allowlist(self) -> dict:
        try:
            if self.allowlist_path.exists():
                return json.loads(self.allowlist_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            self.log.warning("Could not read OpenClaw allowlist; defaulting to block-all.")
        return {"default_policy": "block", "skills": {}, "forbidden_capabilities": []}

    def is_allowed(self, skill_name: str) -> tuple[bool, str]:
        skills = self._allowlist.get("skills", {})
        entry = skills.get(skill_name)
        if not entry or not entry.get("allowed", False):
            return False, "not on allowlist"
        forbidden = set(self._allowlist.get("forbidden_capabilities", []))
        caps = set(entry.get("capabilities", []))
        bad = caps & forbidden
        if bad:
            return False, f"requests forbidden capabilities: {sorted(bad)}"
        return True, "allowed"

    def _audit(self, skill: str, decision: str, status: str) -> None:
        if self.memory is not None and hasattr(self.memory, "log_audit"):
            try:
                self.memory.log_audit(draft_id=skill, action="openclaw_skill_invocation",
                                      agent=self.name, owner_decision=decision, final_status=status)
            except Exception:
                self.log.debug("audit log failed", exc_info=True)

    def run(self, state: Any) -> Any:
        skill = (state.requested_skill or "").strip()
        state.tools_used.append(self.name)
        if not skill:
            state.output = "[openclaw] No skill specified. Use 'skill:<name>' in your request."
            state.final_status = "no_skill_specified"
            return state

        self.log.info("OpenClaw skill requested: %s", skill)
        allowed, why = self.is_allowed(skill)
        if not allowed:
            warning = f"SECURITY WARNING: OpenClaw skill '{skill}' BLOCKED ({why}). Add it to "
            warning += "config/openclaw_allowlist.json (a gated action) to enable."
            self.log.warning(warning)
            state.security_warnings.append(warning)
            state.output = warning
            state.final_status = "blocked_unapproved_skill"
            self._audit(skill, "blocked", "blocked_unapproved_skill")
            return state

        # Allowed -> run via the draft-only registry (still cannot publish/post/etc.).
        result = self.openclaw.handle(Task(name=skill, payload=state.task_meta or {}, requested_by="openclaw_skill_agent"))
        state.output = result.data.get("content", result.detail)
        state.final_status = f"skill_ran:{result.status}"
        self._audit(skill, "allowed", state.final_status)
        self.log.info("OpenClaw skill '%s' executed (draft-only): %s", skill, result.status)
        return state
