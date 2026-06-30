"""Creative Studio CLI (V1a, headless).

    python -m creative demo                       # create a sample project, print its id
    python -m creative show <project_id>          # print a project summary
    python -m creative list                       # list project ids
    python -m creative render <project_id> [--output PATH] [--captions]

Renders write to a LOCAL file only. Nothing is uploaded or published. If ffmpeg/Pillow are not
installed, commands report it clearly instead of failing silently or faking success.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from core.console import enable_utf8_console
from creative.models import Caption, Clip, VideoProject
from creative.providers.ffmpeg_editor import FfmpegVideoEditor
from creative.providers.srt_captions import SrtCaptionProvider
from creative.render import build_caption_cues, build_render_spec
from creative.store import VideoProjectStore


def _demo(store: VideoProjectStore) -> int:
    p = VideoProject(title="Sample Sports Recap", description="V1a demo project (no real media).")
    p.clips = [
        Clip(src="assets/clip1.mp4", in_=0.0, out=5.0, order=0,
             captions=[Caption(0.0, 3.0, "Top play of the night")]),
        Clip(src="assets/clip2.mp4", in_=2.0, out=7.0, order=1,
             captions=[Caption(0.0, 3.0, "What a finish!")]),
    ]
    p.thumbnail = {"template": "sports_basic",
                   "fields": {"title": "TOP PLAYS", "subtitle": "Tonight's Highlights"}}
    p.add_edit("system", "created demo project")
    store.save(p)
    print(f"Created project {p.id} ({len(p.clips)} clips). Render: python -m creative render {p.id}")
    return 0


def _show(store: VideoProjectStore, pid: str) -> int:
    p = store.load(pid)
    print(f"{p.id}  '{p.title}'  status={p.status}  clips={len(p.clips)}  renders={len(p.renders)}")
    for c in p.ordered_clips():
        print(f"  [{c.order}] {c.src}  in={c.in_} out={c.out}  captions={len(c.captions)}")
    print(f"  edit history: {len(p.edit_history)} entries; thumbnail={p.thumbnail or '(none)'}")
    return 0


def _render(store: VideoProjectStore, pid: str, output: str | None, captions: bool) -> int:
    p = store.load(pid)
    out = output or str(store.root / pid / "render_draft.mp4")
    srt_path = None
    if captions:
        cues = build_caption_cues(p)
        if cues:
            srt_path = SrtCaptionProvider().write(cues, store.assets_dir(pid).parent / "captions.srt")
    spec = build_render_spec(p, out, captions_srt=srt_path)
    result = FfmpegVideoEditor().render(spec)
    if result.ok:
        p.add_render(result.output_path, kind="draft", visibility="private")
        p.add_edit("system", "rendered draft", after=result.output_path)
        store.save(p)
        print(f"OK: rendered draft -> {result.output_path} (local; not published)")
        return 0
    print(f"NOT RENDERED: {result.reason}")
    if result.command:
        print("ffmpeg command would have been:\n  " + " ".join(result.command))
    return 1


def main(argv=None) -> int:
    enable_utf8_console()
    parser = argparse.ArgumentParser(prog="creative", description="Sportsverse Creative Studio (V1a)")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("demo")
    sub.add_parser("list")
    sp_show = sub.add_parser("show"); sp_show.add_argument("project_id")
    sp_r = sub.add_parser("render")
    sp_r.add_argument("project_id"); sp_r.add_argument("--output"); sp_r.add_argument("--captions", action="store_true")
    args = parser.parse_args(argv)

    store = VideoProjectStore()
    if args.cmd == "demo":
        return _demo(store)
    if args.cmd == "list":
        ids = store.list_ids()
        print("\n".join(ids) if ids else "(no projects yet — run: python -m creative demo)")
        return 0
    if args.cmd == "show":
        return _show(store, args.project_id)
    if args.cmd == "render":
        return _render(store, args.project_id, args.output, args.captions)
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
