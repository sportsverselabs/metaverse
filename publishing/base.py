"""Shared publishing types.

Adapters return structured results and never raise platform/API failures into
callers. Secrets stay in server-side configuration; result data must stay safe
for dashboard display, logs, and tests.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Protocol


@dataclass
class PublishResult:
    ok: bool
    platform: str
    post_id: str = ""
    url: str = ""
    reason: str = ""
    dry_run: bool = False
    data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class Publisher(Protocol):
    platform: str

    @property
    def configured(self) -> bool:
        ...

    def publish(self, post: dict, *, visibility: str = "private") -> PublishResult:
        ...
