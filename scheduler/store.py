"""File-based persistence for scheduled slots (portable; one JSON per slot)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from core import paths
from core.logging_setup import get_logger
from scheduler.models import ScheduledSlot


class SchedulerStore:
    def __init__(self, base_dir: Path = paths.SCHEDULE_DIR, logger=None) -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.log = logger or get_logger("scheduler.store")

    def _path(self, slot_id: str) -> Path:
        return self.base_dir / f"{slot_id}.json"

    def add(self, slot: ScheduledSlot) -> Path:
        path = self._path(slot.id)
        path.write_text(json.dumps(slot.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
        self.log.info("Proposed slot %s for review %s at %s", slot.id, slot.review_id, slot.scheduled_for)
        return path

    def update(self, slot: ScheduledSlot) -> Path:
        path = self._path(slot.id)
        path.write_text(json.dumps(slot.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
        return path

    def get(self, slot_id: str) -> Optional[ScheduledSlot]:
        path = self._path(slot_id)
        if not path.exists():
            return None
        return ScheduledSlot.from_dict(json.loads(path.read_text(encoding="utf-8")))

    def list(self, *, status: Optional[str] = None) -> list[ScheduledSlot]:
        slots: list[ScheduledSlot] = []
        for path in sorted(self.base_dir.glob("*.json")):
            try:
                slots.append(ScheduledSlot.from_dict(json.loads(path.read_text(encoding="utf-8"))))
            except (json.JSONDecodeError, TypeError):
                self.log.warning("Skipping unreadable slot file: %s", path.name)
        slots.sort(key=lambda s: s.scheduled_for)
        if status is not None:
            slots = [s for s in slots if s.status == status]
        return slots

    def review_ids_with_slots(self) -> set[str]:
        """Review ids that already have a non-cancelled slot (avoid double-scheduling)."""
        from scheduler.models import SLOT_CANCELLED

        return {s.review_id for s in self.list() if s.status != SLOT_CANCELLED}
