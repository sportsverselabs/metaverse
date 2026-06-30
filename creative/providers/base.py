"""Provider interfaces + result types for the Creative Studio.

Mirrors the proven `publishing/base.py` contract: every provider exposes ``.configured`` and returns a
result object (never raises into the caller, never fakes success).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class RenderResult:
    ok: bool
    output_path: Optional[str] = None
    reason: str = ""
    command: list = field(default_factory=list)   # argv used (no secrets — local tool)
    dry_run: bool = False


@dataclass
class ThumbnailResult:
    ok: bool
    output_path: Optional[str] = None
    reason: str = ""


class VideoEditorProvider:
    """assemble/trim/reorder/render. Implementations: FfmpegVideoEditor (+ future MoviePy/Remotion)."""
    name = "video-editor"

    @property
    def configured(self) -> bool:
        raise NotImplementedError

    def render(self, spec: dict) -> RenderResult:
        raise NotImplementedError


class ThumbnailProvider:
    """generate/compose thumbnails. Implementations: PillowThumbnailProvider (+ future AI/Canva)."""
    name = "thumbnail"

    @property
    def configured(self) -> bool:
        raise NotImplementedError

    def generate(self, template: str, fields: dict, output: str) -> ThumbnailResult:
        raise NotImplementedError


class CaptionProvider:
    """transcribe/edit/burn captions. Implementations: SrtCaptionProvider (+ future Whisper)."""
    name = "caption"

    @property
    def configured(self) -> bool:
        raise NotImplementedError
