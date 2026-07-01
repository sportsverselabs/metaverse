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

# V1c: AI revision (DeepSeek) + compliance re-check + review-queue wiring.
_REVISION_TARGETS = {"title", "description", "caption"}


def _compliance_text(p: VideoProject) -> str:
    parts = [p.title, p.description]
    for c in p.ordered_clips():
        parts += [cap.text for cap in c.captions]
    return "\n".join(t for t in parts if t)


def _run_compliance(p: VideoProject) -> dict:
    """Run the Compliance Office over the project's text; store + return the result dict."""
    try:
        from agents.compliance import Compliance
        r = Compliance().review_draft(_compliance_text(p), platform="youtube")
        result = {"verdict": r.verdict, "risk_score": r.risk_score, "passed": r.passed,
                  "notes": r.notes, "checks": r.checks}
    except Exception as exc:  # never break the studio
        result = {"verdict": "error", "risk_score": 100, "passed": False, "notes": str(exc), "checks": {}}
    p.compliance = result
    return result

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
            f"<button class=btnsm onclick=\"studioCaption('{_esc(c.id)}')\">Save caption</button> "
            f"<button class=btnsm onclick=\"studioAction('auto_caption',{{clip:'{_esc(c.id)}'}})\">Auto-caption (Whisper)</button></div>"
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

    # Title/description + AI revision.
    meta_html = (
        f"<div class=row><h4>Title</h4><div class=meta>{_esc(p.title)}</div>"
        f"<div style='margin-top:8px'><button class=btnsm onclick=\"studioRevise('title')\">Request AI revision</button></div></div>"
        f"<div class=row><h4>Description</h4><div class=meta>{_esc(p.description or '(none)')}</div>"
        f"<div style='margin-top:8px'><button class=btnsm onclick=\"studioRevise('description')\">Request AI revision</button></div></div>")

    # Compliance status.
    comp = p.compliance or {}
    if comp:
        ok = comp.get("passed")
        comp_html = (f"<div class=st><span><span class='dot {'ok' if ok else 'warn'}'></span>Compliance</span>"
                     f"<span>risk {_esc(comp.get('risk_score'))} · passed={_esc(ok)} · {_esc(comp.get('verdict'))}</span></div>")
    else:
        comp_html = "<p class=muted>Not checked yet — runs automatically on render, or click below.</p>"

    can_submit = bool(p.compliance.get("passed")) and any(p.renders)
    submit_btn = (f"<button class=btnsm onclick=\"studioAction('submit_for_review')\">Submit for review →</button>"
                  if can_submit else
                  "<span class=muted>Render a draft and pass compliance to enable Submit.</span>")

    # Debug status: engine availability + actual files on disk + statuses.
    caps = _capabilities()
    render_file = next((Path(r["path"]).name for r in reversed(p.renders)
                        if (store.root / pid / Path(r["path"]).name).is_file()), None)
    thumb_ok = bool((p.thumbnail or {}).get("path")) and (store.root / pid / "thumbnail.png").is_file()
    inputs_ok = all((not c.src.startswith("assets/")) or (store.root / pid / c.src).is_file() or Path(c.src).is_file()
                    for c in p.clips) if p.clips else False
    status_html = (
        f"<div class=note><b>Files &amp; status</b> — "
        f"engine: {'ffmpeg ✓' if caps['ffmpeg'] else 'ffmpeg ✗'} / {'Pillow ✓' if caps['pillow'] else 'Pillow ✗'} · "
        f"clips: {len(p.clips)} ({'inputs present' if inputs_ok else 'MISSING input file(s) — render will fail'}) · "
        f"render: {_esc(render_file) if render_file else 'none yet'} · "
        f"thumbnail: {'thumbnail.png ✓' if thumb_ok else 'none yet'} · status: {_esc(p.status)} "
        f"<button class=btnsm onclick=\"openStudio('{_esc(pid)}')\">Refresh status</button></div>")

    return (
        f"<h2>Studio — {_esc(p.title)}</h2>"
        f"<button class=btnsm onclick=\"go('video')\">← Back to projects</button>"
        f"{status_html}"
        f"<h3 style='margin:16px 0 10px'>Preview</h3>{preview}"
        f"<div style='margin-top:14px'>"
        f"<button class=btnsm onclick=\"studioAction('render')\">Render draft</button> "
        f"<button class=btnsm onclick=\"studioAction('thumbnail')\">Generate thumbnail</button></div>"
        f"<h3 style='margin:20px 0 10px'>Title &amp; description</h3>{meta_html}"
        f"<h3 style='margin:20px 0 10px'>Clips</h3>{clips_html}"
        f"<h3 style='margin:20px 0 10px'>Thumbnail</h3>{thumb_html or '<p class=muted>No thumbnail yet.</p>'}"
        f"<h3 style='margin:20px 0 10px'>Compliance</h3>{comp_html}"
        f"<div style='margin-top:8px'><button class=btnsm onclick=\"studioAction('compliance')\">Run compliance check</button></div>"
        f"<h3 style='margin:20px 0 10px'>Decision</h3>"
        f"<div class=note>Submitting sends this to the <b>Approvals</b> queue (gated). Approving &amp; scheduling "
        f"there still does NOT publish — the Phase 5 publisher is separate and owner-gated.</div>"
        f"<div style='margin-top:10px'>{submit_btn} "
        f"<button class='btnsm danger' onclick=\"studioAction('reject')\">Reject</button></div>"
        f"<h3 style='margin:20px 0 10px'>Edit history</h3>"
        f"<div class=meta>{len(p.edit_history)} change(s) logged (incl. AI revisions).</div>")


# ----------------------------------------------------------------------- #
# Actions
# ----------------------------------------------------------------------- #
def _generate_sample_clip(path: Path, *, label: str = "Sportsverse", seconds: int = 5) -> Optional[Path]:
    """Best-effort real sample clip (color + silent audio) via ffmpeg lavfi, so a demo can actually render."""
    import shutil
    import subprocess
    if shutil.which("ffmpeg") is None:
        return None
    path.parent.mkdir(parents=True, exist_ok=True)
    base = ["ffmpeg", "-y", "-f", "lavfi", "-i", f"color=c=0x0b1220:s=1280x720:d={seconds}",
            "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-t", str(seconds),
            "-pix_fmt", "yuv420p", "-c:v", "libx264", "-c:a", "aac", "-shortest", str(path)]
    try:
        r = subprocess.run(base, capture_output=True, text=True, timeout=60)
        return path if r.returncode == 0 and path.is_file() else None
    except Exception:
        return None


def _make_demo(store: VideoProjectStore) -> VideoProject:
    p = VideoProject(title="New Video Project", description="Created in the dashboard.")
    clip = _generate_sample_clip(store.assets_dir(p.id) / "clip1.mp4")
    src = str(clip) if clip else "assets/clip1.mp4"
    p.clips = [Clip(src=src, in_=0.0, out=5.0, order=0,
                    captions=[Caption(0.0, 3.0, "Edit this caption")])]
    p.thumbnail = {"template": "sports_basic", "fields": {"title": "SPORTSVERSE", "subtitle": "Draft"}}
    note = "created project in dashboard" if clip else "created project (no ffmpeg: add real media before rendering)"
    p.add_edit("owner", note)
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
        comp = _run_compliance(p)  # V1c: re-check compliance on every render
        store.save(p)
        _notify(f"🎬 Sportsverse: draft video rendered for '{p.title}' "
                f"(compliance risk {comp['risk_score']}, passed={comp['passed']}) — review in the Studio.")
        return {"message": f"Rendered draft (local, not published). Compliance risk {comp['risk_score']}, "
                           f"passed={comp['passed']}.", "project": pid}

    if action == "thumbnail":
        prov = PillowThumbnailProvider()
        if not prov.configured:
            return {"error": "Pillow not installed on the server (pip install Pillow)."}
        tpl = (p.thumbnail or {}).get("template", "sports_basic")
        fields = (p.thumbnail or {}).get("fields") or {"title": p.title}
        # Save at the PROJECT ROOT (not assets/) so the preview + media route find it by filename.
        out = str(store.root / pid / "thumbnail.png")
        res = prov.generate(tpl, fields, out)
        if not res.ok or not Path(out).is_file():
            return {"error": res.reason or "thumbnail file was not created"}
        p.thumbnail = {"template": tpl, "fields": fields, "path": res.output_path}
        p.add_edit(actor, "generated thumbnail", after=res.output_path)
        store.save(p)
        return {"message": "Thumbnail generated.", "project": pid}

    if action == "auto_caption":
        from creative.providers.whisper_captions import WhisperCaptionProvider
        c = next((c for c in p.clips if c.id == body.get("clip")), None)
        if not c:
            return {"error": "clip not found"}
        prov = WhisperCaptionProvider()
        if not prov.configured:
            return {"error": "Whisper not installed on the server (pip install faster-whisper)."}
        cues = prov.transcribe(c.src)
        if not cues:
            return {"error": "No speech detected or transcription unavailable."}
        c.captions = cues
        p.add_edit("ai", f"auto-captioned clip ({len(cues)} segments)")
        store.save(p)
        return {"message": f"Auto-captioned {len(cues)} segment(s).", "project": pid}

    if action == "compliance":
        comp = _run_compliance(p)
        store.save(p)
        return {"message": f"Compliance: risk {comp['risk_score']}, passed={comp['passed']} "
                           f"({comp['verdict']}).", "project": pid}

    if action == "ai_revision":
        target = (body.get("target") or "title").strip().lower()
        if target not in _REVISION_TARGETS:
            return {"error": "revision target must be title, description, or caption"}
        instruction = (body.get("instruction") or "Make it more engaging and platform-appropriate.").strip()
        clip = None
        if target == "caption":
            clip = next((c for c in p.clips if c.id == body.get("clip")), None)
            if not clip or not clip.captions:
                return {"error": "pick a clip with a caption to revise"}
            current = clip.captions[0].text
        else:
            current = p.title if target == "title" else p.description
        revised = _ai_rewrite(target, current, instruction, p)
        if revised.get("error"):
            return revised
        text = revised["text"]
        if target == "title":
            p.title = text
        elif target == "description":
            p.description = text
        else:
            clip.captions[0].text = text
        p.add_edit("ai", f"AI revised {target}", before=current, after=text)
        store.save(p)
        return {"message": f"AI revised the {target} (draft — review it).", "project": pid}

    if action == "submit_for_review":
        if not any((store.root / pid / Path(r["path"]).name).is_file() for r in p.renders):
            return {"error": "Render a draft first, then submit for review."}
        comp = p.compliance or _run_compliance(p)
        if not comp.get("passed"):
            return {"error": f"Compliance not passed (risk {comp.get('risk_score')}). Revise before submitting."}
        review_id = _submit_to_review(p, comp)
        p.review_id = review_id
        p.status = "in_review"
        p.add_edit(actor, "submitted to owner review queue", after=review_id)
        store.save(p)
        return {"message": f"Submitted to the Approvals queue as {review_id}. "
                           f"Approve & schedule there; publishing stays owner-gated.", "project": pid}

    if action == "reject":
        p.status = "rejected"
        p.add_edit(actor, "owner rejected (draft; not published)")
        store.save(p)
        return {"message": "Project rejected.", "project": pid}

    return {"error": "unknown studio action"}


def _ai_rewrite(target: str, current: str, instruction: str, project: VideoProject) -> dict:
    """Use DeepSeek (via the cost-aware router) to rewrite a title/description/caption. Draft only."""
    try:
        from core.config import load_config
        from providers.model_router import ModelRouter
        system = ("You are a sports-media content editor for Sportsverse. Rewrite the given text per the "
                  "instruction. Keep it truthful, platform-appropriate, and brand-safe. Do NOT invent "
                  "scores, stats, or quotes. Return ONLY the revised text, no preamble.")
        prompt = (f"Field: {target}\nVideo title: {project.title}\nCurrent {target}:\n{current or '(empty)'}\n\n"
                  f"Instruction: {instruction}\n\nRevised {target}:")
        result = ModelRouter(config=load_config()).complete(prompt, task_type="content", system=system)
        if getattr(result, "needs_approval", False):
            return {"error": "This revision would exceed the budget threshold — approve spend first."}
        text = (result.text or "").strip().strip('"')
        if not text:
            return {"error": "AI returned empty text; try a clearer instruction."}
        return {"text": text[:2000]}
    except Exception as exc:
        return {"error": f"AI revision unavailable: {type(exc).__name__}"}


def _submit_to_review(project: VideoProject, comp: dict) -> str:
    """Create a review item for an edited video so it enters the gated owner-review/publish pipeline."""
    from review.models import make_review_item
    from review.store import ReviewStore
    render = project.renders[-1]["path"] if project.renders else ""
    content = (f"VIDEO PROJECT: {project.title}\n\n{project.description}\n\n"
               f"Render (local draft): {render}\nProject id: {project.id}\n"
               f"Captions: " + " | ".join(cap.text for c in project.ordered_clips() for cap in c.captions))
    item = make_review_item(
        skill="video_project", content=content, risk_score=int(comp.get("risk_score", 0)),
        compliance=comp, source_text=f"creative-studio:{project.id}",
        compliance_passed=bool(comp.get("passed")),
    )
    ReviewStore().add(item)
    return item.id


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
