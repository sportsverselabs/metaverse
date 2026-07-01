# Sportsverse — Media & Licensing Policy

**Rule: never publish media unless its license is clearly compatible with commercial use.**
When in doubt, use a labeled placeholder and replace it before launch.

## Allowed sources
- **Public domain** (CC0 / explicitly public domain).
- **Creative Commons** — only with a license that permits commercial use; add attribution if the license requires it (record it in `docs/MEDIA_ATTRIBUTIONS.md`).
- **Licensed stock** you have purchased/licensed for commercial use.
- **Self-generated** graphics (CSS gradients, SVGs, AI-generated where the tool's terms allow commercial use).
- **Unsplash / Pexels / Pixabay** — only when the specific asset's license permits commercial use; keep a link to the source + license.

## Not allowed
- Random "free online" images/video without a clear license.
- Broadcast footage, official league/club media, brand logos, or athlete imagery you don't have rights to.
- Copyrighted music / trending audio without a license (this is the #1 takedown risk on YouTube/TikTok/IG).
- Scraped or reused protected media.
- Any assets, code, images, or text from reference sites (e.g. makemepulse.com) — used only for *design inspiration*, never copied.

## Placeholders
The current website ships with **self-generated placeholders** (CSS gradients) labeled:
> "Sports placeholder image — replace before launch."

Each must be swapped for a properly-licensed asset before going public.

## Compliance gate
The **Compliance agent** (`agents/compliance.py`) already flags copyright / fair-use / FTC-disclosure / music
risks on drafts. Nothing reaches publishing without passing the human approval gate. Real publishing
(Phase 5) must additionally verify media rights per this policy before any upload.

## Attribution log
If any CC-attribution asset is used, record it in `docs/MEDIA_ATTRIBUTIONS.md` (source URL, license, author).

## Generated storyboard visuals (2026-07-01)

The Creative Studio "New from prompt" feature builds 30s drafts from **Sportsverse-generated** visuals
(branded title/beat/CTA cards rendered by ffmpeg). These are safe to use (CC0-equivalent — we create them).
Every clip carries provenance (`Clip.meta.source_kind` = generated / owner_upload / licensed); the editor
shows a media-safety banner. **No real match footage is ever downloaded or fabricated.** Before publishing,
the owner replaces generated placeholders with owner-uploaded (rights asserted) or clearly-licensed clips.
