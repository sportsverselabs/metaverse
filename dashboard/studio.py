"""Creative Studio dashboard surface (V1b).

Renders the studio overview + per-project editor (preview, clip list with reorder/trim, caption edit,
thumbnail), and handles studio edit actions. Edits go through the VideoProject model + store (every change
is logged to the project's append-only edit history). Renders write to LOCAL files only — nothing here
publishes. Approve/AI-revision are intentionally deferred to V1c (shown but clearly labelled).
"""

from __future__ import annotations

import html
import re
from pathlib import Path
from typing import Optional

from creative.models import Caption, Clip, VideoProject
from creative.providers.ffmpeg_editor import FfmpegVideoEditor
from creative.providers.pillow_thumbnail import PillowThumbnailProvider
from creative.providers.srt_captions import SrtCaptionProvider
from creative.render import build_caption_cues, build_render_spec
from creative.store import VideoProjectStore

_ID_RE = re.compile(r"^[A-Za-z0-9_-]+$")
_CONTENT_TYPES = {".mp4": "video/mp4", ".webm": "video/webm", ".png": "image/png",
                  ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".srt": "text/plain; charset=utf-8"}


def _esc(x) -> str:
    return html.escape(str(x))


def _store() -> VideoProjectStore:
    return VideoProjectStore()


def _capabilities() -> dict:
    return {"ffmpeg": FfmpegVideoEditor().configured, "pillow": PillowThumbnailProvider().configured}


# ----------------------------------------------------------------------- #
# Overview
# ----------------------------------------------------------------------- #
def overview_html() -> str:
    store = _store()
    caps = _capabilities()
    cap_note = (f"Render engine: {'ffmpeg ✓' if caps['ffmpeg'] else 'ffmpeg not installed'} · "
                f"Thumbnails: {'Pillow ✓' if caps['pillow'] else 'Pillow not installed'}")
    rows = []
    for pid in store.list_ids():
        try:
            p = store.load(pid)
        except Exception:
            continue
        rows.append(
            f"<div class=row><h4>{_esc(p.title)}</h4>"
            f"<div class=meta>{_esc(pid)} · status {_esc(p.status)} · {len(p.clips)} clips · "
            f"{len(p.renders)} renders</div>"
            f"<div style='margin-top:8px'><button class=btnsm onclick=\"openStudio('{_esc(pid)}')\">Open in studio</button></div></div>")
    listing = "".join(rows) or "<p class=muted>No video projects yet.</p>"
    return (f"<h2>Creative Studio</h2>"
            f"<p class=muted>Preview, edit, and prepare draft videos in-dashboard. Renders are local "
            f"drafts only — nothing is published. {_esc(cap_note)}</p>"
            f"<button class=btnsm onclick=\"studioAction('demo')\">+ New demo project</button>"
            f"<h3 style='margin:18px 0 10px'>Projects</h3>{listing}")


# ----------------------------------------------------------------------- #
# Editor
# ----------------------------------------------------------------------- #
def editor_html(project_id: str) -> str:
    store = _store()
    try:
        p = store.load(project_id)
    except Exception as exc:
        return f"<h2>Creative Studio</h2><div class=note>Could not open project: {_esc(exc)}</div>"

    pid = p.id
    # Preview: latest existing render file.
    preview = "<p class=muted>No render yet — click <b>Render draft</b> below.</p>"
    for r in reversed(p.renders):
        name = Path(r["path"]).name
        if (store.root / pid / name).is_file():
            preview = (f"<video controls style='max-width:100%;border-radius:10px' "
                       f"src='/dashboard/studio/media?project={_esc(pid)}&file={_esc(name)}'></video>"
                       f"<div class=meta>Latest draft ({_esc(r.get('visibility','private'))}, local only)</div>")
            break

    # Clip rows with reorder + trim + caption edit.
    clip_rows = []
    for c in p.ordered_clips():
        cap_text = c.captions[0].text if c.captions else ""
        clip_rows.append(
            f"<div class=row><h4>#{c.order} {_esc(Path(c.src).name)}</h4>"
            f"<div class=meta>{_esc(c.src)}</div>"
            f"<div style='margin-top:8px'>"
            f"<button class=btnsm onclick=\"studioReorder('{_esc(c.id)}','up')\">▲</button> "
            f"<button class=btnsm onclick=\"studioReorder('{_esc(c.id)}','down')\">▼</button>"
            f"</div>"
            f"<div style='margin-top:8px'>trim in "
            f"<input id='in_{_esc(c.id)}' value='{_esc(c.in_)}' size=5> out "
            f"<input id='out_{_esc(c.id)}' value='{_esc('' if c.out is None else c.out)}' size=5> "
            f"<button class=btnsm onclick=\"studioTrim('{_esc(c.id)}')\">Set trim</button></div>"
            f"<div style='margin-top:8px'>caption "
            f"<input id='cap_{_esc(c.id)}' value='{_esc(cap_text)}' size=40> "
            f"<button class=btnsm onclick=\"studioCaption('{_esc(c.id)}')\">Save caption</button></div>"
            f"</div>")
    clips_html = "".join(clip_rows) or "<p class=muted>No clips. Add media files under the project's folder, then re-open.</p>"

    # Thumbnail.
    thumb = p.thumbnail or {}
    thumb_path = thumb.get("path")
    thumb_html = ""
    if thumb_path and (store.root / pid / Path(thumb_path).name).is_file():
        thumb_html = (f"<img style='max-width:320px;border-radius:8px' "
                      f"src='/dashboard/studio/media?project={_esc(pid)}&file={_esc(Path(thumb_path).name)}'>")
    elif thumb.get("fields"):
        thumb_html = f"<div class=meta>Template: {_esc(thumb.get('template','sports_basic'))} · {_esc(thumb['fields'])}</div>"

    return (
        f"<h2>Studio — {_esc(p.title)}</h2>"
        f"<button class=btnsm onclick=\"go('video')\">← Back to projects</button>"
        f"<h3 style='margin:16px 0 10px'>Preview</h3>{preview}"
        f"<div style='margin-top:14px'>"
        f"<button class=btnsm onclick=\"studioAction('render')\">Render draft</button> "
        f"<button class=btnsm onclick=\"studioAction('thumbnail')\">Generate thumbnail</button></div>"
        f"<h3 style='margin:20px 0 10px'>Clips</h3>{clips_html}"
        f"<h3 style='margin:20px 0 10px'>Thumbnail</h3>{thumb_html or '<p class=muted>No thumbnail yet.</p>'}"
        f"<h3 style='margin:20px 0 10px'>Decision</h3>"
        f"<div class=note>Approve / Request AI revision arrive in V1c (with a compliance re-check before "
        f"anything can be scheduled). Nothing here publishes.</div>"
        f"<div style='margin-top:10px'>"
        f"<button class=btnsm onclick=\"studioAction('approve')\">Mark approved (draft)</button> "
        f"<button class='btnsm danger' onclick=\"studioAction('reject')\">Reject</button></div>"
        f"<h3 style='margin:20px 0 10px'>Edit history</h3>"
        f"<div class=meta>{len(p.edit_history)} change(s) logged.</div>")


# ----------------------------------------------------------------------- #
# Actions
# ----------------------------------------------------------------------- #
def _make_demo(store: VideoProjectStore) -> VideoProject:
    p = VideoProject(title="New Video Project", description="Created in the dashboard.")
    p.clips = [Clip(src="assets/clip1.mp4", in_=0.0, out=5.0, order=0,
                    captions=[Caption(0.0, 3.0, "Edit this caption")])]
    p.thumbnail = {"template": "sports_basic", "fields": {"title": "SPORTSVERSE", "subtitle": "Draft"}}
    p.add_edit("owner", "created project in dashboard")
    store.save(p)
    return p


def _f(val, default=None):
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


def studio_action(body: dict, *, actor: str = "owner") -> dict:
    store = _store()
    action = (body.get("action") or "").strip()

    if action == "demo":
        p = _make_demo(store)
        return {"message": "Demo project created.", "project": p.id}

    pid = (body.get("project") or "").strip()
    if not _ID_RE.match(pid):
        return {"error": "invalid project id"}
    try:
        p = store.load(pid)
    except Exception:
        return {"error": "project not found"}

    if action == "reorder":
        clips = p.ordered_clips()
        for i, c in enumerate(clips):
            c.order = i  # normalize
        idx = next((i for i, c in enumerate(clips) if c.id == body.get("clip")), None)
        if idx is None:
            return {"error": "clip not found"}
        swap = idx - 1 if body.get("dir") == "up" else idx + 1
        if 0 <= swap < len(clips):
            clips[idx].order, clips[swap].order = clips[swap].order, clips[idx].order
            p.add_edit(actor, f"reordered clip {body.get('clip')} {body.get('dir')}")
            store.save(p)
        return {"message": "Reordered.", "project": pid}

    if action == "trim":
        c = next((c for c in p.clips if c.id == body.get("clip")), None)
        if not c:
            return {"error": "clip not found"}
        before = {"in": c.in_, "out": c.out}
        c.in_ = _f(body.get("in_"), 0.0) or 0.0
        c.out = _f(body.get("out"), None)
        p.add_edit(actor, "trimmed clip", before=before, after={"in": c.in_, "out": c.out})
        store.save(p)
        return {"message": "Trim updated.", "project": pid}

    if action == "caption":
        c = next((c for c in p.clips if c.id == body.get("clip")), None)
        if not c:
            return {"error": "clip not found"}
        text = (body.get("text") or "").strip()
        if c.captions:
            c.captions[0].text = text
        else:
            c.captions = [Caption(0.0, min(3.0, c.duration or 3.0), text)]
        p.add_edit(actor, "edited caption", after=text)
        store.save(p)
        return {"message": "Caption saved.", "project": pid}

    if action == "render":
        out = str(store.root / pid / "render_draft.mp4")
        srt = None
        cues = build_caption_cues(p)
        if cues:
            srt = SrtCaptionProvider().write(cues, store.root / pid / "captions.srt")
        spec = build_render_spec(p, out, captions_srt=srt)
        result = FfmpegVideoEditor().render(spec)
        if not result.ok:
            return {"error": f"Render failed: {result.reason}"}
        p.add_render(result.output_path, kind="draft", visibility="private")
        p.add_edit(actor, "rendered draft", after=result.output_path)
        store.save(p)
        _notify(f"🎬 Sportsverse: draft video rendered for '{p.title}' — review it in the dashboard Studio.")
        return {"message": "Rendered draft (local, not published).", "project": pid}

    if action == "thumbnail":
        prov = PillowThumbnailProvider()
        if not prov.configured:
            return {"error": "Pillow not installed on the server (pip install Pillow)."}
        tpl = (p.thumbnail or {}).get("template", "sports_basic")
        fields = (p.thumbnail or {}).get("fields") or {"title": p.title}
        out = str(store.assets_dir(pid) / "thumbnail.png")
        res = prov.generate(tpl, fields, out)
        if not res.ok:
            return {"error": res.reason}
        p.thumbnail = {"template": tpl, "fields": fields, "path": res.output_path}
        p.add_edit(actor, "generated thumbnail", after=res.output_path)
        store.save(p)
        return {"message": "Thumbnail generated.", "project": pid}

    if action in ("approve", "reject"):
        p.status = "approved" if action == "approve" else "rejected"
        p.add_edit(actor, f"owner {action} (draft; not published)")
        store.save(p)
        note = ("Marked approved as a DRAFT. Publishing still requires V1c compliance + the gated publisher."
                if action == "approve" else "Project rejected.")
        return {"message": note, "project": pid}

    return {"error": "unknown studio action"}


def _notify(message: str) -> None:
    """Best-effort Telegram 'draft ready' ping; never raises."""
    try:
        from core.config import load_config
        from integrations.telegram_bot import JarvisTelegramBot
        cfg = load_config()
        if cfg.secret("TELEGRAM_BOT_TOKEN"):
            JarvisTelegramBot(cfg).send(message)
    except Exception:
        pass


# ----------------------------------------------------------------------- #
# Media serving (session-gated in the server; path-traversal safe here)
# ----------------------------------------------------------------------- #
def media_path(project_id: str, filename: str) -> Optional[tuple]:
    """Resolve (path, content_type) for a project asset, or None if invalid/missing/outside the project."""
    if not _ID_RE.match(project_id or ""):
        return None
    base = (_store().root / project_id).resolve()
    target = (base / (filename or "")).resolve()
    if base != target and base not in target.parents:
        return None
    if not target.is_file():
        return None
    return target, _CONTENT_TYPES.get(target.suffix.lower(), "application/octet-stream")
