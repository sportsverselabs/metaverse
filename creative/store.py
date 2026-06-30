"""VideoProject storage — one JSON file per project under reports/video/<id>/ (runtime, gitignored)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from creative.models import VideoProject

DEFAULT_ROOT = Path("reports") / "video"


class VideoProjectStore:
    def __init__(self, root: Optional[Path | str] = None) -> None:
        self.root = Path(root) if root else DEFAULT_ROOT

    def path(self, project_id: str) -> Path:
        return self.root / project_id / "project.json"

    def assets_dir(self, project_id: str) -> Path:
        d = self.root / project_id / "assets"
        d.mkdir(parents=True, exist_ok=True)
        return d

    def save(self, project: VideoProject) -> Path:
        p = self.path(project.id)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(project.to_dict(), indent=2), encoding="utf-8")
        return p

    def load(self, project_id: str) -> VideoProject:
        p = self.path(project_id)
        if not p.exists():
            raise FileNotFoundError(f"no video project '{project_id}' at {p}")
        return VideoProject.from_dict(json.loads(p.read_text(encoding="utf-8")))

    def list_ids(self) -> list[str]:
        if not self.root.exists():
            return []
        return sorted(d.name for d in self.root.iterdir() if (d / "project.json").exists())
