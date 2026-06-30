# PLUGIN / PROVIDER MAP — Sportsverse OS

> **Rule:** never hard-code concrete tools (Canva, CapCut, Premiere, Synthesia, a specific LLM…).
> Everything is reached through a **provider interface** so implementations swap without touching
> callers. Cost order for every provider: **local/open-source → DeepSeek → existing infra → free API →
> paid only if unavoidable** (and any paid path is owner-gated).

## Provider interfaces
| Interface | Purpose | Built? | V1 implementation (planned/actual) | Future impls (gated) |
|-----------|---------|--------|-------------------------------------|----------------------|
| **LLMProvider** | text: drafts, hooks, titles, descriptions, revision, reasoning | **Built** | `providers/deepseek_provider.py` (default) via `providers/model_router.py`; `core/providers/{mock,openai,anthropic}` | NVIDIA/Nemotron (`providers/nemotron_provider.py`, optional/off), OpenAI, Claude |
| **PublishingProvider** | push approved content to a platform (gated) | **Built** | `publishing/{youtube,instagram,tiktok}.py` + `publishing/base.py` + `service.py` | more platforms behind gates |
| **ResearchProvider** | trends/web/Reddit/X/YouTube research | **Not built** | `last30days`-style skill + free sources; sports already via Hub | paid research APIs (gated) |
| **VideoEditorProvider** | assemble/trim/reorder/render/probe video | **Built** | `FfmpegVideoEditor` (live on VPS) | Remotion renderer, FFmpeg.wasm (client) — deferred |
| **ThumbnailProvider** | generate/compose thumbnails | **Built** | `PillowThumbnailProvider` (live on VPS) | AI image gen / Canva behind a provider (gated) |
| **CaptionProvider** | transcribe/edit/burn captions | **Built** | `SrtCaptionProvider` (text + FFmpeg burn) + `WhisperCaptionProvider` (local `faster-whisper`, optional) | hosted ASR (gated) |
| **DataProvider (sports)** | scores/news/standings | **Built** | `sports/` ESPN + API-Football via `SportsDataHub` | more leagues/providers |
| **NotifyProvider** | owner alerts | **Built** | `integrations/telegram_bot.py`, `integrations/email_report.py` | — |
| **StorageProvider** | memory/knowledge persistence | **Partial** | `memory/manager.py` (file), `orchestration/journal.py` | searchable knowledge library |

## Existing abstraction proof points
- **LLM:** `model_router.select()` picks DeepSeek vs Nemotron by task/complexity, with mock fallback — a
  clean, working provider switch. Keep this as the template for the new providers.
- **Publishing:** `publishing/base.py` defines `PublishResult` + a publisher protocol with `.configured`
  and `.publish(post, visibility)`; adapters are selected by platform in `PublishingService`. **Mirror
  this exact shape** for `VideoEditorProvider` / `ThumbnailProvider` / `CaptionProvider`.

## Provider selection & config
- Implementation chosen via `.env` / config (e.g. `VIDEO_EDITOR_PROVIDER=ffmpeg`,
  `THUMBNAIL_PROVIDER=pillow`, `CAPTION_PROVIDER=srt`), defaulting to the local/open-source impl.
- A provider reports `.configured`; if its tool/credential is missing it returns a clear
  "not configured" result — **never a fake success** (same contract as `EmailReporter` and the
  publishing adapters).
- Tests inject a fake transport/binary so they run **offline and deterministically** (the
  `ESPNClient(fetch=...)` / publishing-transport pattern).

## NVIDIA / Nemotron
Optional **future** `LLMProvider` only. Already wired as off-by-default (`NEMOTRON_ENABLED=false` →
fallback to DeepSeek). Do **not** make it core unless a low-cost API or self-hosted/local path is
verified. DeepSeek remains the foundational LLM.

## What this map tells the next builder
The two **established** provider families (LLM, Publishing) are the blueprint. The creative studio adds
**three new local-first providers** (VideoEditor, Thumbnail, Caption) plus a **ResearchProvider** for the
Research department — all behind interfaces, all open-source-first, none hard-coding a paid tool.
