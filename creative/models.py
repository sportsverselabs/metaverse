"""Creative Studio data model.

A ``VideoProject`` is the editable unit the owner reviews. It holds an ordered clip list (with trim
points and captions), title cards / lower-thirds / overlays, a thumbnail spec, render outputs, and an
**append-only edit history** (satisfies "save edit history" + "all owner decisions logged"). Pure data
+ (de)serialization — no rendering here.
"""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime

STATUS_DRAFT = "draft"
STATUS_RENDERED = "rendered"
STATUS_IN_REVIEW = "in_review"
STATUS_APPROVED = "approved"


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _new_id(prefix: str) -> str:
    return f"{prefix}-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}"


@dataclass
class Caption:
    start: float          # seconds, relative to the clip
    end: float
    text: str

    def to_dict(self) -> dict:
        return {"start": self.start, "end": self.end, "text": self.text}


# Media provenance (license safety): where a clip's visuals came from.
SOURCE_GENERATED = "generated"      # Sportsverse-generated visuals (safe placeholder; CC0-equivalent)
SOURCE_OWNER_UPLOAD = "owner_upload"  # footage the owner provided (owner asserts the right to use it)
SOURCE_LICENSED = "licensed"        # clearly-licensed stock (license_url required)
_SAFE_SOURCES = {SOURCE_GENERATED, SOURCE_OWNER_UPLOAD, SOURCE_LICENSED}


@dataclass
class Clip:
    src: str                              # path to source media
    id: str = field(default_factory=lambda: _new_id("clip"))
    in_: float = 0.0                      # trim start (seconds)
    out: float | None = None              # trim end (seconds); None = to end
    order: int = 0
    captions: list[Caption] = field(default_factory=list)
    # Provenance: {source_kind, license, license_url, role, note}. Empty = unknown (treated as unsafe).
    meta: dict = field(default_factory=dict)

    @property
    def duration(self) -> float | None:
        return None if self.out is None else max(0.0, self.out - self.in_)

    @property
    def source_kind(self) -> str:
        return (self.meta or {}).get("source_kind", "")

    @property
    def license_safe(self) -> bool:
        """True only if the clip's visuals are clearly safe to use (generated/owner/licensed)."""
        kind = self.source_kind
        if kind == SOURCE_LICENSED:
            return bool((self.meta or {}).get("license_url"))
        return kind in {SOURCE_GENERATED, SOURCE_OWNER_UPLOAD}

    def to_dict(self) -> dict:
        return {"id": self.id, "src": self.src, "in": self.in_, "out": self.out,
                "order": self.order, "captions": [c.to_dict() for c in self.captions], "meta": self.meta}

    @classmethod
    def from_dict(cls, d: dict) -> "Clip":
        return cls(src=d["src"], id=d.get("id") or _new_id("clip"), in_=float(d.get("in", 0.0)),
                   out=(None if d.get("out") is None else float(d["out"])),
                   order=int(d.get("order", 0)),
                   captions=[Caption(**c) for c in d.get("captions", [])],
                   meta=d.get("meta", {}) or {})


@dataclass
class TitleCard:
    text: str
    style: str = "default"
    position: str = "center"
    duration: float = 2.0

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Overlay:
    kind: str                  # "lower_third" | "logo" | "text" | ...
    data: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {"kind": self.kind, "data": self.data}


@dataclass
class VideoProject:
    title: str
    id: str = field(default_factory=lambda: _new_id("vproj"))
    description: str = ""
    status: str = STATUS_DRAFT
    created: str = field(default_factory=_now)
    updated: str = field(default_factory=_now)
    clips: list[Clip] = field(default_factory=list)
    title_cards: list[TitleCard] = field(default_factory=list)
    lower_thirds: list[Overlay] = field(default_factory=list)
    overlays: list[Overlay] = field(default_factory=list)
    thumbnail: dict = field(default_factory=dict)        # {template, fields, path}
    renders: list[dict] = field(default_factory=list)    # [{path, ts, kind, visibility}]
    edit_history: list[dict] = field(default_factory=list)
    compliance: dict = field(default_factory=dict)
    review_id: str = ""

    # ---- editing helpers -------------------------------------------- #
    def ordered_clips(self) -> list[Clip]:
        return sorted(self.clips, key=lambda c: c.order)

    def add_edit(self, actor: str, action: str, before=None, after=None) -> None:
        """Append-only history. actor = 'owner' | 'ai' | 'system'."""
        self.edit_history.append({"ts": _now(), "actor": actor, "action": action,
                                  "before": before, "after": after})
        self.updated = _now()

    def add_render(self, path: str, *, kind: str = "draft", visibility: str = "private") -> None:
        self.renders.append({"path": path, "ts": _now(), "kind": kind, "visibility": visibility})
        self.status = STATUS_RENDERED
        self.updated = _now()

    # ---- (de)serialization ------------------------------------------ #
    def to_dict(self) -> dict:
        return {
            "id": self.id, "title": self.title, "description": self.description,
            "status": self.status, "created": self.created, "updated": self.updated,
            "clips": [c.to_dict() for c in self.clips],
            "title_cards": [t.to_dict() for t in self.title_cards],
            "lower_thirds": [o.to_dict() for o in self.lower_thirds],
            "overlays": [o.to_dict() for o in self.overlays],
            "thumbnail": self.thumbnail, "renders": self.renders,
            "edit_history": self.edit_history, "compliance": self.compliance,
            "review_id": self.review_id,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "VideoProject":
        p = cls(title=d.get("title", "Untitled"), id=d.get("id") or _new_id("vproj"))
        p.description = d.get("description", "")
        p.status = d.get("status", STATUS_DRAFT)
        p.created = d.get("created", _now())
        p.updated = d.get("updated", p.created)
        p.clips = [Clip.from_dict(c) for c in d.get("clips", [])]
        p.title_cards = [TitleCard(**t) for t in d.get("title_cards", [])]
        p.lower_thirds = [Overlay(**o) for o in d.get("lower_thirds", [])]
        p.overlays = [Overlay(**o) for o in d.get("overlays", [])]
        p.thumbnail = d.get("thumbnail", {})
        p.renders = d.get("renders", [])
        p.edit_history = d.get("edit_history", [])
        p.compliance = d.get("compliance", {})
        p.review_id = d.get("review_id", "")
        return p
