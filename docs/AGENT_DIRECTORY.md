# SportVerse Labs — Agent Directory

Every agent and what it does. Hermes is the boss; nothing publishes/spends without owner approval.

| Agent | File | What it does |
|---|---|---|
| **Hermes** (Executive Officer) | `agents/hermes.py` | Routes work, tracks cost/risk, requires approval for production actions, reviews outputs, reports. Final decision-maker. |
| **Jarvis** (Interface) | `agents/jarvis.py` | Telegram/CLI/voice command layer; turns requests into structured tasks; plain-English status. No executive decisions. |
| **Research** | `agents/research_agent.py` | Finds topics/trends/angles; competitor watch; research briefs (DeepSeek). |
| **Content** | `agents/content_agent.py` | Articles, scripts, captions, titles, hashtags; platform-specific (DeepSeek). |
| **Video** | `agents/video_agent.py` | Video concept + 30–45s script + metadata; CapCut editing note. Draft only. |
| **Social Publishing** | `agents/social_publishing_agent.py` | Prepares posts for YT/IG/TikTok/website. Never posts without approval + Phase 5 capability. |
| **Approval** | `agents/approval_agent.py` | Unified approve / reject / request-edit / upload-edit / "Are you sure?" confirm. Publishes nothing. |
| **Analytics** | `agents/analytics_agent.py` | Tracks performance; best/worst; learns owner preferences from approvals/edits. |
| **Security** | `agents/security_agent.py` | Watches logs/secrets/backups/uptime; alerts to Telegram. |
| **Deployment** | `agents/deployment_agent.py` | VPS checklist; asks for the next missing credential; tracks deploy status. |
| **GitHub Backup** | `agents/github_backup_agent.py` | Safe backups; protects secrets; push commands; never commits `.env`. |
| **DNS / Website** | `agents/dns_website_agent.py` | DNS records to connect the domain; verifies resolution/SSL. |
| **Dashboard** | `agents/dashboard_agent.py` | Assembles the read-only owner dashboard data. |
| **Documentation** | `agents/documentation_agent.py` | Keeps architecture/user-manual/deploy/recovery/account docs + this directory. |
| **OpenClaw Skill** | `agents/openclaw_skill_agent.py` | Controlled skill adapter; allowlist only; never the orchestrator. |
| **Nemotron Reasoning** | `agents/nemotron_reasoning_agent.py` | Optional high-reasoning specialist; off by default; falls back to DeepSeek. |
| **Compliance** | `agents/compliance.py` | Per-dimension review (policy/copyright/fair-use/FTC/brand/per-platform); never auto-approves. |
| **Sentinel** | `agents/sentinel.py` | Skill-permission integrity / drift monitor. |
| **Archivist** | `agents/archivist.py` | Institutional memory + handoff keeper. |
