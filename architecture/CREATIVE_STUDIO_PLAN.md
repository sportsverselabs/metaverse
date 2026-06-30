# CREATIVE STUDIO PLAN — Dashboard-native Video & Thumbnail Editing

> **Plan only.** No production code is built from this document yet. It defines the architecture for
> a dashboard-native creative studio so the owner can preview, edit, and approve draft videos **inside
> the Sportsverse dashboard** — without logging into CapCut, Canva, Synthesia, or any paid tool for the
> basic workflow. Open-source / local first; everything behind provider interfaces.

## 1. Owner workflow (target)
1. Telegram notification: "Draft video ready for review."
2. Owner opens the dashboard → **Video Review / Creative Studio**.
3. Preview the rendered draft.
4. Edit: trim/reorder clips, edit captions, title/lower-thirds/overlays, title/description/thumbnail.
5. Request AI revision (DeepSeek for text; render pipeline re-runs).
6. Approve / reject / approve-for-gated-scheduling.
Every step is logged; nothing publishes without owner approval and a compliance re-check.

## 2. Cost-first technology decision
Following the cost rule (local/open-source → DeepSeek → existing infra → free APIs → paid only if
unavoidable):

| Concern | V1 choice (build) | Why | Deferred / future |
|---------|-------------------|-----|-------------------|
| Video render/assembly | **FFmpeg** (server-side) via a thin Python wrapper, optionally **MoviePy** | Free, installed on the VPS, battle-tested, scriptable | — |
| Editing UI | **Browser clip-list editor** (server-rendered HTML + small vanilla JS), preview via `<video>` | Matches the existing dependency-free dashboard; no build step | Full WASM timeline later |
| In-browser preview trims | Native `<video>` + JS in/out markers (non-destructive markers, render server-side) | No heavy deps; instant | **FFmpeg.wasm** for client-side scrub/cut later |
| Captions | **CaptionProvider**: edit `.srt`/`.vtt` text; burn-in via FFmpeg `subtitles` filter; optional Whisper(.cpp) auto-transcribe later | Text editing is free; auto-caption is local/optional | Hosted ASR only if owner opts in |
| Thumbnails | **ThumbnailProvider**: **Pillow** (raster) + optional SVG template → PNG | Free, deterministic, brand-templated | Canva/AI image gen behind a provider, owner-gated |
| Title cards / lower-thirds / overlays | FFmpeg `drawtext`/`overlay` + PNG/SVG assets from templates | Free, repeatable, brand-controlled | Remotion (React renderer) if motion graphics become a priority |
| Text/revision intelligence | **DeepSeek** via existing `LLMProvider` | Already the default low-cost LLM | OpenAI/Claude optional |

**Remotion / FireRed-OpenStoryline-style note:** Remotion (React + Node renderer) gives polished
programmatic motion graphics but adds a Node toolchain + heavier render cost — **defer to V2** behind
`VideoEditorProvider` if/when motion templates are needed. FFmpeg+MoviePy cover V1 fully.

## 3. Provider interfaces (no tool lock-in)
All studio capability is accessed through interfaces (see `PLUGIN_PROVIDER_MAP.md`); the dashboard and
agents never import a concrete tool directly:
- `VideoEditorProvider` — `assemble(clips)`, `trim(clip, in, out)`, `reorder(order)`, `render(spec) -> path`, `probe(path)`.
  - V1 impl: `FfmpegVideoEditor` (+ optional `MoviePyVideoEditor`).
- `ThumbnailProvider` — `generate(template, fields) -> path`, `from_frame(video, ts, overlays) -> path`.
  - V1 impl: `PillowThumbnailProvider`.
- `CaptionProvider` — `transcribe(audio) -> cues` (optional), `edit(cues) -> cues`, `burn(video, cues) -> path`.
  - V1 impl: `SrtCaptionProvider` (+ optional `WhisperCaptionProvider`).
- `LLMProvider` — existing (DeepSeek default) for hooks/titles/descriptions/revision.

## 4. Data model (proposed)
A **VideoProject** persisted as JSON under `reports/video/<project_id>/` (runtime, gitignored), plus
assets on disk:
```
VideoProject{ id, title, description, status, created, updated,
  clips:[{id, src, in, out, order, captions:[{start,end,text}]}],
  title_cards:[{text, style, position, duration}],
  lower_thirds:[...], overlays:[...],
  thumbnail:{template, fields, path},
  renders:[{path, ts, kind:'draft|final', visibility}],
  edit_history:[{ts, actor:'owner|ai', action, before, after}],
  compliance:{...last result...}, review_id }
```
- **Edit history** is append-only (satisfies "save edit history" + "all owner decisions logged").
- A render spec is derived from the project and handed to `VideoEditorProvider.render`.

## 5. Agents/skills under Hermes (department Hermes pattern)
These are **department roles routed by Hermes**, executing **whitelisted OpenClaw skills** — not new
top-level orchestrators:
- **Video Hermes** — assembly, clip trimming, caption burn, render, export packaging (calls `VideoEditorProvider`/`CaptionProvider`).
- **Creative Hermes** — thumbnail design, layout, typography, brand styling, title cards (calls `ThumbnailProvider`).
- **Content Hermes** — hooks, scripts, titles, descriptions, CTAs (calls `LLMProvider`=DeepSeek).
- **Compliance Hermes** — platform/copyright/reused-content/monetization/brand-safety re-check on every edited render (existing Compliance Office).
- **Sentinel** — blocks unsafe tools, blocks auto-publish, audits any new skill/plugin before use.
- **OpenClaw** — executes only whitelisted skills; no public posting without owner approval; no unapproved installs.

## 6. Dashboard surface
Replace the placeholder **Video Review** section with **Creative Studio**:
- Preview pane (`<video>` of latest draft render).
- Clip list (reorder, trim in/out markers, delete) — server-rendered rows + JS.
- Caption editor (editable cue text).
- Title/description fields; thumbnail preview + template fields.
- Buttons: **Render draft**, **Request AI revision**, **Approve**, **Reject**, **Approve for scheduling**.
- All actions POST to session-gated `/dashboard/action` (reuse the existing auth + confirm pattern).
- Long renders run as a background job; Telegram notifies when the new draft is ready.

## 7. Pipeline (edited video → approval)
```
owner edits project -> Video/Creative Hermes render (FFmpeg) -> Compliance Hermes re-check
   -> draft render shown in dashboard + Telegram ping
   -> owner Approve -> review item -> scheduler (gated) -> (Phase 5 publisher, owner-gated) -> YouTube private
```
No path skips compliance or owner approval. Renders default to local files; nothing uploads without the
existing gated publishing step.

## 8. Safety (LOCKED — unchanged)
No auto-publishing; no public posting without approval; edited content re-runs compliance; renders are
local until an explicit gated publish; no unapproved OpenClaw skills; no secrets in logs; no paid-tool
lock-in (everything behind providers).

## 9. Build phases (when approved to build)
- **V1a (foundation):** ✅ **BUILT (2026-06-30)** — `creative/` package: `VideoProject` model + `VideoProjectStore`,
  provider interfaces (`VideoEditorProvider`/`ThumbnailProvider`/`CaptionProvider`) with local impls
  (`FfmpegVideoEditor`, `PillowThumbnailProvider`, `SrtCaptionProvider`), render-spec + caption-offset
  builders, and a headless CLI (`python -m creative demo|show|list|render`). 14 offline tests (ffmpeg/Pillow
  injected/guarded — suite needs neither). Renders go to local files only; nothing publishes. No UI yet.
  **Note:** real rendering needs `ffmpeg` on the host; thumbnails need `pip install Pillow` — both report
  "not configured" clearly when absent.
- **V1b (studio UI):** ✅ **BUILT + DEPLOYED (2026-06-30)** — `dashboard/studio.py`: Creative Studio
  section (overview + per-project editor: preview, clip reorder/trim, caption edit, thumbnail, render
  draft). Routes `/dashboard/studio`, `/dashboard/studio/media` (path-traversal safe), `/dashboard/studio/action`.
  Telegram "draft ready" ping on render. **FFmpeg + Pillow installed on the VPS; a real render + thumbnail
  were verified end-to-end on the server.** Renders are local drafts only — nothing publishes. (Render is
  synchronous for now — fine for short drafts; can move to a job queue later.)
- **V1c (AI + compliance loop):** ✅ **BUILT + DEPLOYED (2026-06-30)** — "Request AI revision" (DeepSeek
  rewrites title/description/caption, draft-only + budget-gated + logged), **compliance re-check on every
  render** (+ on demand; stored on the project), and **Submit for review** (gated on a render existing AND
  compliance passed → creates a `ReviewItem` in the owner Approvals queue, entering the existing
  review/scheduler/gated-publisher pipeline). Verified live on the VPS with real DeepSeek. Nothing publishes.
- **V2 (optional):** FFmpeg.wasm client scrubbing, Whisper auto-captions, Remotion motion templates — each behind its provider, owner-gated for any cost.

## 10. Does the current architecture support this? (answer)
**Yes, with additive work — no rewrite.** The dashboard (server-rendered sections + session-gated
actions), the review/approval/scheduler gates, the journal/audit, OpenClaw whitelist, and the provider
pattern (already proven by `providers/` and `publishing/`) all extend cleanly. The only genuinely new
pieces are the **video provider implementations**, the **VideoProject store**, and the **Creative
Studio UI** — all local/open-source. FFmpeg must be present on the VPS (free; one apt install).
