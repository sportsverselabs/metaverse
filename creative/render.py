"""Turn a VideoProject into a render spec (and optionally a burned-in caption .srt).

Pure functions so they're testable without ffmpeg. The actual render is done by a VideoEditorProvider.
"""

from __future__ import annotations

from typing import Optional

from creative.models import Caption, VideoProject


def build_caption_cues(project: VideoProject) -> list:
    """Flatten per-clip captions onto the final timeline, offset by cumulative clip durations.

    Returns [] if any clip with captions has an unknown duration (out=None), since the offset can't be
    computed reliably — captions are then skipped rather than placed wrong.
    """
    cues: list[Caption] = []
    offset = 0.0
    for clip in project.ordered_clips():
        if clip.captions and clip.duration is None:
            return []  # can't place captions without a known clip duration
        for c in clip.captions:
            cues.append(Caption(start=offset + c.start, end=offset + c.end, text=c.text))
        offset += clip.duration or 0.0
    return cues


def build_render_spec(project: VideoProject, output: str, *,
                      captions_srt: Optional[str] = None, fps: Optional[int] = None) -> dict:
    """Build the dict consumed by VideoEditorProvider.render()."""
    inputs = [{"path": c.src, "in": c.in_, "out": c.out} for c in project.ordered_clips()]
    spec: dict = {"inputs": inputs, "output": output}
    if captions_srt:
        spec["captions_srt"] = captions_srt
    if fps:
        spec["fps"] = fps
    return spec
