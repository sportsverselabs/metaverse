"""File-based, portable persistence for review items.

Layout under ``reports/review/``:
    <id>.json           active items (ready / revision_requested / approved_for_future_publish)
    archive/<id>.json   rejected items (archived with reason)

One JSON file per item — easy to inspect, diff, back up, and move with the project.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from core import paths
from core.logging_setup import get_logger
from review.models import STATUS_READY, ReviewItem


class ReviewStore:
    def __init__(self, base_dir: Path = paths.REVIEW_DIR, logger=None) -> None:
        self.base_dir = Path(base_dir)
        self.archive_dir = self.base_dir / "archive"
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        self.log = logger or get_logger("review.store")

    # paths
    def _active_path(self, item_id: str) -> Path:
        return self.base_dir / f"{item_id}.json"

    def _archive_path(self, item_id: str) -> Path:
        return self.archive_dir / f"{item_id}.json"

    @staticmethod
    def _write(path: Path, item: ReviewItem) -> Path:
        path.write_text(json.dumps(item.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
        return path

    # operations
    def add(self, item: ReviewItem) -> Path:
        path = self._write(self._active_path(item.id), item)
        self.log.info("Queued review item %s (skill=%s, risk=%s)", item.id, item.skill, item.risk_score)
        return path

    def update(self, item: ReviewItem) -> Path:
        """Rewrite an active item in place (status change without archiving)."""
        return self._write(self._active_path(item.id), item)

    def archive(self, item: ReviewItem) -> Path:
        """Move an item to the archive (used for rejected drafts)."""
        active = self._active_path(item.id)
        if active.exists():
            active.unlink()
        path = self._write(self._archive_path(item.id), item)
        self.log.info("Archived review item %s", item.id)
        return path

    def get(self, item_id: str) -> Optional[ReviewItem]:
        for path in (self._active_path(item_id), self._archive_path(item_id)):
            if path.exists():
                return ReviewItem.from_dict(json.loads(path.read_text(encoding="utf-8")))
        return None

    def list(self, *, status: Optional[str] = None, include_archived: bool = False) -> list[ReviewItem]:
        dirs = [self.base_dir] + ([self.archive_dir] if include_archived else [])
        items: list[ReviewItem] = []
        for directory in dirs:
            for path in sorted(directory.glob("*.json")):
                try:
                    items.append(ReviewItem.from_dict(json.loads(path.read_text(encoding="utf-8"))))
                except (json.JSONDecodeError, TypeError):
                    self.log.warning("Skipping unreadable review file: %s", path.name)
        items.sort(key=lambda i: i.created)
        if status is not None:
            items = [i for i in items if i.status == status]
        return items

    def list_pending(self) -> list[ReviewItem]:
        """Items waiting for the owner (status == ready_for_owner_review)."""
        return self.list(status=STATUS_READY)
