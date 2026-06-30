"""FFmpeg-backed video editor (V1a).

Assembles an ordered list of trimmed clips into one render, optionally burning a subtitle (.srt) file.
The ffmpeg command is built by a pure function (`build_ffmpeg_command`) so it is fully unit-testable
without ffmpeg installed; the actual invocation goes through an injectable ``runner`` (default:
subprocess), so tests run offline. Renders write to a LOCAL file only — nothing is uploaded.
"""

from __future__ import annotations

import shutil
from typing import Callable, Optional

from creative.providers.base import RenderResult, VideoEditorProvider

# runner(argv) -> (returncode, stderr_text)
Runner = Callable[[list], "tuple[int, str]"]


def build_ffmpeg_command(spec: dict) -> list:
    """Build an ffmpeg argv from a render spec.

    spec = {
      "inputs": [{"path": str, "in": float?, "out": float?}, ...],   # ordered
      "output": str,
      "captions_srt": str?,      # optional path to a .srt to burn into the video
      "fps": int?,               # optional
    }
    Uses filter_complex trim+concat so per-clip in/out points are honored.
    """
    inputs = spec.get("inputs") or []
    if not inputs:
        raise ValueError("render spec has no inputs")
    output = spec["output"]

    args = ["ffmpeg", "-y"]
    for inp in inputs:
        args += ["-i", inp["path"]]

    filters, labels = [], []
    for idx, inp in enumerate(inputs):
        start = float(inp.get("in", 0) or 0)
        end = inp.get("out", None)
        vtrim = f"trim=start={start}" + (f":end={float(end)}" if end is not None else "")
        atrim = f"atrim=start={start}" + (f":end={float(end)}" if end is not None else "")
        filters.append(f"[{idx}:v]{vtrim},setpts=PTS-STARTPTS[v{idx}]")
        filters.append(f"[{idx}:a]{atrim},asetpts=PTS-STARTPTS[a{idx}]")
        labels.append(f"[v{idx}][a{idx}]")

    n = len(inputs)
    srt = spec.get("captions_srt")
    vlabel = "[vcat]" if srt else "[vout]"
    filters.append("".join(labels) + f"concat=n={n}:v=1:a=1{vlabel}[aout]")
    if srt:
        # Escape the path for ffmpeg's subtitles filter (colons/backslashes/quotes).
        safe = str(srt).replace("\\", "/").replace(":", "\\:").replace("'", "\\'")
        filters.append(f"[vcat]subtitles='{safe}'[vout]")

    args += ["-filter_complex", ";".join(filters), "-map", "[vout]", "-map", "[aout]"]
    if spec.get("fps"):
        args += ["-r", str(int(spec["fps"]))]
    args += ["-c:v", "libx264", "-c:a", "aac", output]
    return args


def _subprocess_runner(argv: list) -> "tuple[int, str]":
    import subprocess
    proc = subprocess.run(argv, capture_output=True, text=True)
    return proc.returncode, (proc.stderr or "")


class FfmpegVideoEditor(VideoEditorProvider):
    name = "ffmpeg"

    def __init__(self, runner: Optional[Runner] = None) -> None:
        # Inject a runner in tests; in production it defaults to subprocess when ffmpeg is present.
        self._runner = runner

    @property
    def configured(self) -> bool:
        return self._runner is not None or shutil.which("ffmpeg") is not None

    def render(self, spec: dict) -> RenderResult:
        try:
            cmd = build_ffmpeg_command(spec)
        except (ValueError, KeyError) as exc:
            return RenderResult(False, reason=f"bad render spec: {exc}")

        runner = self._runner
        if runner is None:
            if shutil.which("ffmpeg") is None:
                return RenderResult(False, reason="ffmpeg not installed (apt install ffmpeg)", command=cmd)
            runner = _subprocess_runner

        try:
            rc, err = runner(cmd)
        except Exception as exc:  # never raise into the studio
            return RenderResult(False, reason=f"render failed: {type(exc).__name__}", command=cmd)
        if rc != 0:
            return RenderResult(False, reason=f"ffmpeg exited {rc}: {err.strip()[:200]}", command=cmd)
        return RenderResult(True, output_path=spec["output"], command=cmd)
