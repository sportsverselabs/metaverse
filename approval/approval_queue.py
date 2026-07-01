"""Approval queue and the catalogue of gated actions.

Every gated action must be approved by the owner before it can happen. Requests are stored as
one JSON file per request under ``reports/approvals/`` (gitignored runtime data).
"""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any, Optional

from core import paths
from core.logging_setup import get_logger

# Actions that ALWAYS require human approval (Phase 4 safety rule).
GATED_ACTIONS = frozenset({
    "publish_content",
    "send_email",
    "website_change",
    "spend_over_threshold",
    "install_openclaw_skill",
    "vps_config_change",
    "public_post",
    "payment_settings_change",
})

# Keyword hints -> gated action, used to detect intent in a natural-language request.
_ACTION_HINTS = {
    "publish_content": ("publish", "go live"),
    "public_post": ("post to", "post on", "tweet", "public post", "upload to"),
    "send_email": ("send email", "email the", "send an email", "newsletter"),
    "website_change": ("change the website", "edit the site", "update the page", "deploy site"),
    "vps_config_change": ("vps", "server config", "nginx", "ssh", "reconfigure server"),
    "payment_settings_change": ("payment", "banking", "stripe", "payout", "billing settings"),
    "install_openclaw_skill": ("install skill", "add skill", "enable skill"),
    "spend_over_threshold": (),  # set programmatically by the cost router, not by keywords
}

APPROVAL_PENDING = "pending"
APPROVAL_APPROVED = "approved"
APPROVAL_REJECTED = "rejected"


_PUBLIC_RELEASE_ACTIONS = {"publish_content", "public_post"}
_PUBLIC_RELEASE_NEGATIONS = (
    "do not publish",
    "don't publish",
    "dont publish",
    "never publish",
    "not publish",
    "no publishing",
    "without publishing",
    "do not post",
    "don't post",
    "dont post",
    "never post",
    "not post",
    "not a public post",
    "not public post",
    "no posting",
    "without posting",
)


def _negates_public_release(text: str) -> bool:
    """True when the user explicitly asks for draft-only / no-public-release work."""
    return any(phrase in text for phrase in _PUBLIC_RELEASE_NEGATIONS)


def detect_gated_actions(text: str) -> list[str]:
    """Return gated actions implied by a natural-language request (keyword heuristic)."""
    t = " ".join((text or "").lower().split())
    found = []
    negated_public_release = _negates_public_release(t)
    for action, hints in _ACTION_HINTS.items():
        if action in _PUBLIC_RELEASE_ACTIONS and negated_public_release:
            continue
        if any(h in t for h in hints):
            found.append(action)
    return found


@dataclass
class ApprovalRequest:
    id: str
    action: str
    reason: str
    task_id: str = ""
    details: dict = field(default_factory=dict)
    status: str = APPROVAL_PENDING
    created: str = ""
    updated: str = ""
    history: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "ApprovalRequest":
        return cls(**data)


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


class ApprovalQueue:
    def __init__(self, base_dir: Path = paths.APPROVALS_DIR, memory=None, logger=None) -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.memory = memory
        self.log = logger or get_logger("approval")

    def _path(self, req_id: str) -> Path:
        return self.base_dir / f"{req_id}.json"

    def request(self, action: str, reason: str, *, task_id: str = "", details: Optional[dict] = None) -> ApprovalRequest:
        req = ApprovalRequest(
            id=f"ap-{date.today().isoformat()}-{uuid.uuid4().hex[:8]}",
            action=action, reason=reason, task_id=task_id, details=details or {},
            status=APPROVAL_PENDING, created=_now(), updated=_now(),
        )
        req.history.append({"ts": _now(), "action": "requested", "notes": reason})
        self._write(req)
        self.log.info("Approval requested: %s for '%s' (%s)", req.id, action, reason)
        self._audit(req, "approval_requested")
        return req

    def _write(self, req: ApprovalRequest) -> Path:
        path = self._path(req.id)
        path.write_text(json.dumps(req.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
        return path

    def get(self, req_id: str) -> Optional[ApprovalRequest]:
        path = self._path(req_id)
        if not path.exists():
            return None
        return ApprovalRequest.from_dict(json.loads(path.read_text(encoding="utf-8")))

    def list(self, *, status: Optional[str] = None) -> list[ApprovalRequest]:
        out = []
        for p in sorted(self.base_dir.glob("*.json")):
            try:
                out.append(ApprovalRequest.from_dict(json.loads(p.read_text(encoding="utf-8"))))
            except (json.JSONDecodeError, TypeError):
                continue
        out.sort(key=lambda r: r.created)
        if status:
            out = [r for r in out if r.status == status]
        return out

    def approve(self, req_id: str, *, by: str = "owner") -> ApprovalRequest:
        req = self._require(req_id)
        req.status = APPROVAL_APPROVED
        req.updated = _now()
        req.history.append({"ts": _now(), "action": "approved", "by": by})
        self._write(req)
        self.log.info("Approved %s (%s). NOTE: approval records intent; execution is still owner-gated.", req.id, req.action)
        self._audit(req, "approval_approved")
        return req

    def reject(self, req_id: str, reason: str = "", *, by: str = "owner") -> ApprovalRequest:
        req = self._require(req_id)
        req.status = APPROVAL_REJECTED
        req.updated = _now()
        req.history.append({"ts": _now(), "action": "rejected", "by": by, "notes": reason})
        self._write(req)
        self._audit(req, "approval_rejected")
        return req

    def _require(self, req_id: str) -> ApprovalRequest:
        req = self.get(req_id)
        if req is None:
            raise KeyError(f"approval request '{req_id}' not found")
        return req

    def _audit(self, req: ApprovalRequest, action: str) -> None:
        if self.memory is not None and hasattr(self.memory, "log_audit"):
            try:
                self.memory.log_audit(draft_id=req.task_id or req.id, action=action, agent="approval",
                                      owner_decision=req.status, final_status=req.status)
            except Exception:
                self.log.debug("audit log failed", exc_info=True)
