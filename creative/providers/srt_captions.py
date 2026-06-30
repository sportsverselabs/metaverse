"""SRT caption provider (V1a).

Pure-Python parse/format of SubRip (.srt) cues so caption text is fully editable and testable offline.
Burning captions into video is handled by the FFmpeg editor (subtitles filter) — this provider owns the
text and the .srt file.
"""

from __future__ import annotations

from creative.providers.base import CaptionProvider
from creative.models import Caption


def _fmt_ts(seconds: float) -> str:
    seconds = max(0.0, float(seconds))
    ms = int(round((seconds - int(seconds)) * 1000))
    s = int(seconds)
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{sec:02d},{ms:03d}"


def _parse_ts(ts: str) -> float:
    ts = ts.strip().replace(".", ",")
    hms, _, ms = ts.partition(",")
    h, m, s = (int(x) for x in hms.split(":"))
    return h * 3600 + m * 60 + s + (int(ms or 0) / 1000.0)


def format_srt(cues: list) -> str:
    """cues: list of Caption or dicts with start/end/text -> SRT text."""
    out = []
    for i, c in enumerate(cues, 1):
        start = c.start if isinstance(c, Caption) else c["start"]
        end = c.end if isinstance(c, Caption) else c["end"]
        text = c.text if isinstance(c, Caption) else c["text"]
        out.append(f"{i}\n{_fmt_ts(start)} --> {_fmt_ts(end)}\n{text}\n")
    return "\n".join(out).strip() + ("\n" if out else "")


def parse_srt(text: str) -> list:
    """SRT text -> list[Caption]."""
    cues, block = [], []
    for line in (text or "").splitlines() + [""]:
        if line.strip() == "":
            if len(block) >= 2 and "-->" in block[1]:
                start_s, _, end_s = block[1].partition("-->")
                body = "\n".join(block[2:]).strip()
                cues.append(Caption(start=_parse_ts(start_s), end=_parse_ts(end_s), text=body))
            block = []
        else:
            block.append(line)
    return cues


class SrtCaptionProvider(CaptionProvider):
    name = "srt"

    @property
    def configured(self) -> bool:
        return True  # pure Python; no external dependency

    def write(self, cues: list, path) -> str:
        from pathlib import Path
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(format_srt(cues), encoding="utf-8")
        return str(p)
