"""Memory manager.

Minimal, functional, file-based memory that matches ``memory_schema.md``: one markdown
file per memory, with YAML-ish frontmatter, stored under ``memory/store/``. No external
dependencies and no network — fully portable.

Phase 1 scope: basic create / read / list / delete and a naive substring ``recall``.
Smarter retrieval (embeddings / semantic search) is a later-phase upgrade and is marked
with TODOs. Never store secrets here (see security_policy.md).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from core import paths
from core.logging_setup import get_logger

VALID_TYPES = {"owner", "feedback", "project", "reference", "agent"}
_SLUG_RE = re.compile(r"[^a-z0-9]+")


def slugify(name: str) -> str:
    """Turn an arbitrary name into a safe kebab-case filename stem."""
    slug = _SLUG_RE.sub("-", name.strip().lower()).strip("-")
    return slug or "untitled"


@dataclass
class Memory:
    name: str
    description: str
    type: str
    content: str
    path: Path


class MemoryManager:
    def __init__(self, store_dir: Path = paths.MEMORY_STORE, logger=None) -> None:
        self.store_dir = store_dir
        self.log = logger or get_logger("memory")
        self.store_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------ #
    # Write
    # ------------------------------------------------------------------ #
    def remember(
        self,
        name: str,
        content: str,
        *,
        mem_type: str = "project",
        description: str = "",
        owner_agent: Optional[str] = None,
    ) -> Path:
        """Create or update a memory file. Returns its path."""
        if mem_type not in VALID_TYPES:
            raise ValueError(f"invalid memory type '{mem_type}'; expected one of {sorted(VALID_TYPES)}")
        slug = slugify(name)
        path = self.store_dir / f"{slug}.md"
        today = date.today().isoformat()
        created = today
        if path.exists():
            existing = self._parse(path)
            created = existing.get("created", today) if existing else today

        front = [
            "---",
            f"name: {slug}",
            f"description: {description or name}",
            f"type: {mem_type}",
            f"created: {created}",
            f"updated: {today}",
        ]
        if owner_agent:
            front.append(f"owner_agent: {owner_agent}")
        front.append("---")
        path.write_text("\n".join(front) + "\n\n" + content.strip() + "\n", encoding="utf-8")
        self.log.info("Stored memory '%s' (%s)", slug, mem_type)
        return path

    # ------------------------------------------------------------------ #
    # Read
    # ------------------------------------------------------------------ #
    def get(self, name: str) -> Optional[Memory]:
        path = self.store_dir / f"{slugify(name)}.md"
        if not path.exists():
            return None
        meta = self._parse(path) or {}
        body = self._body(path)
        return Memory(
            name=meta.get("name", slugify(name)),
            description=meta.get("description", ""),
            type=meta.get("type", "project"),
            content=body,
            path=path,
        )

    def list_memories(self) -> list[str]:
        return sorted(p.stem for p in self.store_dir.glob("*.md"))

    def recall(self, query: str, limit: int = 5) -> list[Memory]:
        """Naive substring search over description + body.

        TODO(later-phase): replace with embedding / semantic search.
        """
        q = query.lower().strip()
        hits: list[Memory] = []
        for p in sorted(self.store_dir.glob("*.md")):
            meta = self._parse(p) or {}
            body = self._body(p)
            haystack = (meta.get("description", "") + "\n" + body).lower()
            if q and q in haystack:
                hits.append(Memory(meta.get("name", p.stem), meta.get("description", ""),
                                   meta.get("type", "project"), body, p))
            if len(hits) >= limit:
                break
        return hits

    def forget(self, name: str) -> bool:
        path = self.store_dir / f"{slugify(name)}.md"
        if path.exists():
            path.unlink()
            self.log.info("Forgot memory '%s'", slugify(name))
            return True
        return False

    # ------------------------------------------------------------------ #
    # Event log (append-only audit trail of tasks/outputs/warnings/decisions)
    # ------------------------------------------------------------------ #
    def log_event(self, kind: str, summary: str, data: Optional[dict] = None,
                  *, on_date: Optional[str] = None) -> Path:
        """Append a one-line event to a daily log file under the store.

        Used for the audit trail (task received, skill chosen, sentinel verdict,
        compliance result, decision). Never pass secrets in here.
        """
        day = on_date or date.today().isoformat()
        path = self.store_dir / f"events-{day}.md"
        if not path.exists():
            path.write_text(f"# Event log {day}\n\n", encoding="utf-8")
        ts = datetime.now().strftime("%H:%M:%S")
        line = f"- {ts} [{kind}] {summary}"
        if data:
            try:
                line += "  | " + json.dumps(data, default=str, ensure_ascii=False)
            except (TypeError, ValueError):
                line += "  | (unserialisable data)"
        with path.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")
        return path

    def read_events(self, on_date: Optional[str] = None) -> str:
        """Return the raw daily event log text (empty string if none)."""
        day = on_date or date.today().isoformat()
        path = self.store_dir / f"events-{day}.md"
        return path.read_text(encoding="utf-8") if path.exists() else ""

    # ------------------------------------------------------------------ #
    # Structured audit log (one JSON record per action)
    # ------------------------------------------------------------------ #
    def log_audit(
        self,
        *,
        draft_id: str,
        action: str,
        agent: str = "",
        owner_decision: str = "",
        compliance_score: Optional[int] = None,
        final_status: str = "",
        on_date: Optional[str] = None,
    ) -> Path:
        """Append a structured audit record (JSON line) with all required fields.

        Fields: timestamp, draft_id, action, agent, owner_decision, compliance_score,
        final_status. Never pass secrets in here.
        """
        day = on_date or date.today().isoformat()
        path = self.store_dir / f"audit-{day}.jsonl"
        record = {
            "ts": datetime.now().isoformat(timespec="seconds"),
            "draft_id": draft_id,
            "action": action,
            "agent": agent,
            "owner_decision": owner_decision,
            "compliance_score": compliance_score,
            "final_status": final_status,
        }
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
        return path

    def read_audit(self, on_date: Optional[str] = None) -> str:
        """Return the raw daily audit log text (JSON lines; empty string if none)."""
        day = on_date or date.today().isoformat()
        path = self.store_dir / f"audit-{day}.jsonl"
        return path.read_text(encoding="utf-8") if path.exists() else ""

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    @staticmethod
    def _parse(path: Path) -> Optional[dict[str, str]]:
        """Parse the simple ``key: value`` frontmatter block. Returns None if absent."""
        text = path.read_text(encoding="utf-8")
        if not text.startswith("---"):
            return None
        end = text.find("\n---", 3)
        if end == -1:
            return None
        meta: dict[str, str] = {}
        for line in text[3:end].strip().splitlines():
            if ":" in line:
                key, _, value = line.partition(":")
                meta[key.strip()] = value.strip()
        return meta

    @staticmethod
    def _body(path: Path) -> str:
        text = path.read_text(encoding="utf-8")
        if text.startswith("---"):
            end = text.find("\n---", 3)
            if end != -1:
                return text[end + 4:].strip()
        return text.strip()
