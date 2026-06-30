"""Creative Studio provider interfaces + local-first implementations.

Interfaces (no tool lock-in): VideoEditorProvider, ThumbnailProvider, CaptionProvider.
V1a local impls: FfmpegVideoEditor, PillowThumbnailProvider, SrtCaptionProvider.
Each reports ``.configured`` and returns a clear "not configured" result instead of a fake success.
"""

from creative.providers.base import (CaptionProvider, RenderResult, ThumbnailProvider,
                                      ThumbnailResult, VideoEditorProvider)
from creative.providers.ffmpeg_editor import FfmpegVideoEditor, build_ffmpeg_command
from creative.providers.pillow_thumbnail import PillowThumbnailProvider, build_layout
from creative.providers.srt_captions import SrtCaptionProvider, format_srt, parse_srt

__all__ = [
    "VideoEditorProvider", "ThumbnailProvider", "CaptionProvider", "RenderResult", "ThumbnailResult",
    "FfmpegVideoEditor", "build_ffmpeg_command",
    "PillowThumbnailProvider", "build_layout",
    "SrtCaptionProvider", "parse_srt", "format_srt",
]
