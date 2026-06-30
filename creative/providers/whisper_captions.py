"""Whisper caption provider (V2 — local auto-transcription).

Optional, local, open-source auto-captioning behind the existing CaptionProvider interface. Uses
``faster-whisper`` (CTranslate2) if installed; otherwise reports not-configured (never a fake success).
The transcription call is wrapped so it can be injected in tests — no model download in CI.

Install (optional, owner choice): ``pip install faster-whisper``. CPU-only is fine for short clips.
"""

from __future__ import annotations

from typing import Callable, Optional

from creative.models import Caption
from creative.providers.base import CaptionProvider


class WhisperCaptionProvider(CaptionProvider):
    name = "whisper"

    def __init__(self, model_size: str = "base", transcriber: Optional[Callable] = None) -> None:
        self._model_size = model_size
        self._transcriber = transcriber   # inject in tests: (audio_path) -> list[(start,end,text)]

    @property
    def configured(self) -> bool:
        if self._transcriber is not None:
            return True
        try:
            import faster_whisper  # noqa: F401
            return True
        except Exception:
            return False

    def transcribe(self, audio_or_video_path: str) -> list:
        """Return a list of Caption cues. [] if not configured (caller falls back to manual captions)."""
        if not self.configured:
            return []
        run = self._transcriber or self._default_transcribe
        try:
            segments = run(audio_or_video_path)
        except Exception:
            return []
        return [Caption(start=float(s), end=float(e), text=str(t).strip()) for (s, e, t) in segments]

    def _default_transcribe(self, path: str):
        from faster_whisper import WhisperModel
        model = WhisperModel(self._model_size, device="cpu", compute_type="int8")
        segments, _info = model.transcribe(path)
        return [(seg.start, seg.end, seg.text) for seg in segments]
