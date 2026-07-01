"""Turn a Hermes video prompt into a Creative Studio VideoProject.

Media-license safety (LOCKED): this NEVER downloads or fabricates real match footage. It builds a
prompt-matched storyboard from **Sportsverse-generated visuals** (branded title/beat/CTA cards rendered
by ffmpeg) — safe to use — and marks every clip's provenance. The owner replaces the generated
placeholders with owner-uploaded or clearly-licensed footage before publishing. Grounded soccer ideas
come from the Sports Data Hub (no invented scores/quotes). Renders are local drafts; nothing publishes.
"""

from __future__ import annotations

import shutil
import subprocess
import textwrap
from pathlib import Path
from typing import Callable, Optional

from core.logging_setup import get_logger
from creative.models import Caption, Clip, VideoProject, SOURCE_GENERATED

_log = get_logger("creative.storyboard")

_FONT_CANDIDATES = (
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
)


def _find_font() -> Optional[str]:
    return next((f for f in _FONT_CANDIDATES if Path(f).is_file()), None)


def _wrap(text: str, width: int = 22) -> str:
    return "\n".join(textwrap.fill(line, width) for line in (text or "").splitlines() or [""])


def _render_scene_ffmpeg(path: Path, text: str, seconds: float) -> Optional[Path]:
    """Render one branded text card (color bg + centered text + brand bar). Returns path or None."""
    if shutil.which("ffmpeg") is None:
        return None
    path.parent.mkdir(parents=True, exist_ok=True)
    txt = path.with_suffix(".txt")
    txt.write_text(_wrap(text), encoding="utf-8")  # textfile avoids escaping colons/quotes/newlines
    draw = (f"drawtext=textfile='{txt.as_posix()}':fontcolor=white:fontsize=52:"
            f"x=(w-text_w)/2:y=(h-text_h)/2:line_spacing=16")
    font = _find_font()
    if font:
        draw += f":fontfile='{font}'"
    filt = f"drawbox=x=0:y=0:w=iw:h=10:color=0x27E0A0:t=fill,{draw}"
    cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", f"color=c=0x0b1220:s=1280x720:d={seconds}",
           "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-vf", filt, "-t", str(seconds),
           "-pix_fmt", "yuv420p", "-c:v", "libx264", "-c:a", "aac", "-shortest", str(path)]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if r.returncode == 0 and path.is_file():
            return path
        _log.warning("scene render failed rc=%s: %s", r.returncode, (r.stderr or "")[-200:])
        return None
    except Exception as exc:
        _log.error("scene render crashed: %s", type(exc).__name__)
        return None


def plan_scenes(prompt: str, context, *, seconds: int = 30, n_beats: int = 3) -> list[dict]:
    """Build a prompt-matched scene list (hook → beats → CTA) whose durations sum to ``seconds``."""
    from sports.context import SportsContext
    _, _, scope = SportsContext.sport_scope(prompt)
    try:
        ideas = context.highlight_ideas(prompt, n=n_beats)
    except Exception:
        ideas = []
    beats = ideas or [{"title": f"{scope} highlight #{i + 1}", "angle": "", "basis": "evergreen"}
                      for i in range(n_beats)]

    hook_sec = 4
    remaining = max(6, seconds - hook_sec - 5)          # leave >=5s for the CTA
    per = max(3, remaining // len(beats))
    scenes = [{"role": "hook", "text": f"{scope.upper()}\nHIGHLIGHTS",
               "caption": "Top plays to watch", "seconds": hook_sec, "basis": ""}]
    used = hook_sec
    for idea in beats:
        scenes.append({"role": "beat", "text": idea["title"],
                       "caption": idea.get("angle") or idea["title"],
                       "seconds": per, "basis": idea.get("basis", "")})
        used += per
    scenes.append({"role": "cta", "text": f"Follow Platinum Clips\nfor more {scope}",
                   "caption": "Subscribe for more", "seconds": max(3, seconds - used), "basis": ""})
    return scenes


def build_from_prompt(prompt: str, *, store=None, context=None, seconds: int = 30,
                      scene_renderer: Optional[Callable] = None) -> VideoProject:
    """Create + save a VideoProject of generated scenes matching ``prompt``. Nothing publishes."""
    from creative.store import VideoProjectStore
    from sports.context import SportsContext
    store = store or VideoProjectStore()
    if context is None:
        context = SportsContext()
    _, _, scope = SportsContext.sport_scope(prompt)
    render_scene = scene_renderer or _render_scene_ffmpeg

    scenes = plan_scenes(prompt, context, seconds=seconds)
    p = VideoProject(
        title=f"{scope.title()} Highlights — {seconds}s draft",
        description=(f"Prompt: {prompt}\n\nVISUALS: Sportsverse-generated placeholders (safe to use). "
                     "No real match footage is included — replace scenes with owner-uploaded or "
                     "clearly-licensed clips before publishing."))
    assets = store.assets_dir(p.id)
    for i, sc in enumerate(scenes):
        dest = assets / f"scene{i}.mp4"
        made = render_scene(dest, sc["text"], sc["seconds"])
        p.clips.append(Clip(
            src=str(made) if made else str(dest), in_=0.0, out=float(sc["seconds"]), order=i,
            captions=[Caption(0.0, min(3.0, float(sc["seconds"])), sc.get("caption") or sc["text"])],
            meta={"source_kind": SOURCE_GENERATED, "license": "Sportsverse-generated (safe placeholder)",
                  "role": sc["role"], "basis": sc.get("basis", "")}))
    p.thumbnail = {"template": "sports_basic",
                   "fields": {"title": f"{scope.upper()} HIGHLIGHTS", "subtitle": "Top 3 to watch"}}
    p.add_edit("hermes", f"built {seconds}s storyboard from prompt", after=(prompt or "")[:140])
    store.save(p)
    return p
