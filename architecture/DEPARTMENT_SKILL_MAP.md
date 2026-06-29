# DEPARTMENT SKILL MAP — Sportsverse OS

> Skills are organized into **department skill packs**, loaded through the whitelist registry
> (`skills/registry.py` + `config/openclaw_allowlist.json`) and executed **only** by OpenClaw under
> Hermes. Rule: *do not think in random GitHub skills — think in reusable department packs.* A skill
> may be shared across departments. All skills are **draft-only** unless a capability is explicitly
> approved; none may publish, post, email, spend, install, run shell, touch secrets/DB, or modify code.

## Department → role (Hermes) → skill pack
| Department | Hermes role | Skill pack (proposed) | Built today? |
|------------|-------------|------------------------|--------------|
| Executive | **Hermes (CEO)** | routing, cost control, approval enforcement | **Built** |
| Integrity | **Sentinel** | tool/skill audit, drift scan, block-unsafe | Partial |
| Continuity | **Archivist** | handoff write, memory tidy, knowledge index | Partial |
| Compliance Office | **Compliance Hermes** | platform/copyright/reuse/monetization/brand-safety review | **Built** (heuristic) |
| Sports Data | (Hub, not LLM) | scoreboard/news/standings/live/injuries/transfers fetch | **Built** |
| Research | **Research Hermes** | `sports_topic_research_draft`, trend discovery (`last30days`), competitor research | Partial |
| Content | **Content Hermes** | hooks, scripts, titles, descriptions, CTAs, captions text | **Built** (drafts) |
| Video | **Video Hermes** | assemble, trim, reorder, caption-burn, render, export | **Not built** |
| Creative | **Creative Hermes** | thumbnail, title cards, lower-thirds, brand styling | **Not built** |
| Social | **Social Hermes** | platform post packaging (behind publishing gates) | Partial (code) |
| Marketing | **Marketing Hermes** | SEO, hashtags, posting-time strategy, growth ideas | Not built |
| Website | **Website Hermes** | site copy/sections, DNS/SSL verify | Partial |
| Community | **Community Hermes** | template-only comment/DM replies | Not built |
| Commerce | **Commerce Hermes** | affiliate product research/tracking | Not built |
| Analytics | **Analytics Hermes** | metrics ingest, what-worked summaries, preference learning | Partial |
| Development | **Dev Hermes** | code drafts, test drafts (no apply) | Partial |
| Tech Scout | **Scout Hermes** | evaluate new tools/skills/providers (recommend, never install) | Not built |

## Skill pack structure (proposed convention)
```
skills/
  registry.py            # whitelist registry (exists)
  base.py                # DraftSkill base (exists)
  packs/
    research_pack.py     # research-department skills
    content_pack.py      # content-department skills
    video_pack.py        # video-department skills (call VideoEditorProvider)
    creative_pack.py     # thumbnail/title-card skills (call ThumbnailProvider)
    compliance_pack.py   # review skills
    analytics_pack.py    # metrics/summary skills
```
Each pack registers its skills with `name, purpose, department(s), risk, capabilities[], requires_approval`.
The existing six draft skills (`sports_topic_research_draft`, `video_idea_draft`, `script_outline_draft`,
`affiliate_product_research_draft`, `compliance_review_draft`, `daily_report_draft`) become the seed of
the research/content/compliance/analytics packs — **no rewrite, just reorganized + extended.**

## Reuse examples (cross-department)
- A `summarize_draft` skill is used by Research, Content, Analytics, and Reports.
- A `brand_style_lookup` skill is used by Creative (thumbnails) and Website (site copy).
- A `caption_text_draft` skill is used by Content and Video.

## Rules (LOCKED)
1. Only whitelisted skills run; default policy = block.
2. Adding/installing a skill is a **gated action** (Sentinel audit + owner approval).
3. Skills never publish/post/email/spend/install/shell/secret/DB.
4. Capabilities that touch providers (video/thumbnail/caption) are **draft/render-to-local-file only** —
   never upload; publishing stays in the separate owner-gated publisher.
5. Every skill invocation is logged (OpenClaw + journal).
