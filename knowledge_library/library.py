"""Knowledge Library — Sportsverse's research/idea/source memory.

A simple, dependency-free store the departments (via Hermes) can write to and search: article notes,
sources, video ideas, competitor research. File-based JSON under ``knowledge_library/store/`` (runtime,
gitignored). Search is a transparent keyword score (no external index/service).
"""

from __future__ import annotations

import json
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

KINDS = {"note", "article", "source", "idea", "competitor"}
DEFAULT_ROOT = Path("knowledge_library") / "store"

_WORD = re.compile(r"[a-z0-9]+")


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _tokens(text: str) -> list[str]:
    return _WORD.findall((text or "").lower())


class KnowledgeLibrary:
    def __init__(self, root: Optional[Path | str] = None) -> None:
        self.root = Path(root) if root else DEFAULT_ROOT
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, entry_id: str) -> Path:
        return self.root / f"{entry_id}.json"

    def add(self, kind: str, title: str, body: str = "", *, tags=None, source: str = "") -> str:
        kind = kind if kind in KINDS else "note"
        entry_id = f"kb-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}"
        entry = {"id": entry_id, "kind": kind, "title": title, "body": body,
                 "tags": list(tags or []), "source": source, "created": _now()}
        self._path(entry_id).write_text(json.dumps(entry, indent=2), encoding="utf-8")
        return entry_id

    def get(self, entry_id: str) -> Optional[dict]:
        p = self._path(entry_id)
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None

    def remove(self, entry_id: str) -> bool:
        p = self._path(entry_id)
        if p.exists():
            p.unlink()
            return True
        return False

    def list(self, kind: Optional[str] = None) -> list[dict]:
        out = []
        for p in sorted(self.root.glob("kb-*.json")):
            try:
                e = json.loads(p.read_text(encoding="utf-8"))
            except (ValueError, OSError):
                continue
            if kind is None or e.get("kind") == kind:
                out.append(e)
        return sorted(out, key=lambda e: e.get("created", ""), reverse=True)

    def search(self, query: str, *, limit: int = 10) -> list[dict]:
        """Transparent keyword score: title x3, tags x2, body x1. Returns entries with a 'score'."""
        terms = set(_tokens(query))
        if not terms:
            return []
        scored = []
        for e in self.list():
            title_t = _tokens(e.get("title", ""))
            tag_t = _tokens(" ".join(e.get("tags", [])))
            body_t = _tokens(e.get("body", ""))
            score = (3 * sum(t in terms for t in title_t)
                     + 2 * sum(t in terms for t in tag_t)
                     + sum(t in terms for t in body_t))
            if score:
                scored.append({**e, "score": score})
        return sorted(scored, key=lambda e: e["score"], reverse=True)[:limit]
