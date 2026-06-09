"""Agent journal — structured JSONL log of every orchestrated task.

Appends one JSON record per task to ``logs/agent_journal.jsonl`` with: timestamp, task id, user
request, selected route, model used, estimated tokens, estimated cost, tools used, approval
status, compliance score, and final output preview. No secrets are written here.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from core import paths
from core.logging_setup import get_logger


class AgentJournal:
    def __init__(self, path: Optional[Path] = None, logger=None) -> None:
        self.path = path or paths.AGENT_JOURNAL
        self.log = logger or get_logger("journal")
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, record: dict) -> Path:
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
        return self.path

    def read(self, limit: Optional[int] = None) -> list[dict]:
        if not self.path.exists():
            return []
        rows: list[dict] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return rows[-limit:] if limit else rows
