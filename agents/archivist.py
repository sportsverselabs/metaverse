"""Archivist — institutional memory & handoff keeper (skeleton).

The Archivist is responsible for continuity: it records what happened, keeps the
memory store tidy, and maintains the handoff file so any future agent can resume the
project cold. It is the agent embodiment of the continuity rules in PROJECT_DNA.md.

Phase 1 status: SKELETON. Memory writes go through the (functional, minimal)
MemoryManager when one is injected; handoff writing is a stub that points at the file.
"""

from __future__ import annotations

from datetime import date

from agents.base import AgentResult, BaseAgent, STATUS_OK, Task
from core import paths


class Archivist(BaseAgent):
    name = "archivist"
    role = "Institutional Memory & Handoff Keeper"
    reports_to = "hermes"

    def remember(self, name: str, content: str, *, mem_type: str = "project", description: str = "") -> AgentResult:
        """Store a fact via the injected MemoryManager."""
        if self.memory is None:
            return self.not_implemented("memory store (no MemoryManager injected)")
        path = self.memory.remember(name, content, mem_type=mem_type, description=description)
        return AgentResult(self.name, STATUS_OK, f"remembered '{name}'", data={"path": str(path)})

    def note_handoff(self, summary: str) -> AgentResult:
        """SKELETON: record a handoff note.

        Real implementation should append a structured entry to
        ``reports/handoff/latest_handoff.md``. The skeleton only reports where it would
        write, to avoid clobbering the human-maintained handoff during Phase 1.
        """
        self.log.info("note_handoff (skeleton) on %s: %s", date.today().isoformat(), summary[:80])
        return AgentResult(
            self.name,
            STATUS_OK,
            "handoff note acknowledged (skeleton — not written)",
            data={"handoff_file": str(paths.LATEST_HANDOFF)},
        )

    def handle(self, task: Task) -> AgentResult:
        if task.name == "remember":
            p = task.payload
            return self.remember(
                p.get("name", "untitled"),
                p.get("content", ""),
                mem_type=p.get("type", "project"),
                description=p.get("description", ""),
            )
        if task.name in {"handoff", "note_handoff"}:
            return self.note_handoff(task.payload.get("summary", ""))
        return self.not_implemented(f"archivist task '{task.name}'")
