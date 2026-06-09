# OWNER_ACTION_REQUIRED.md

> Things **only you (the owner)** can do. A coding agent cannot do these for you.
> Each item has beginner-friendly steps. Check items off as you complete them.
> Last updated: 2026-06-08

---

## How this file works
- Nothing here blocks running what's already built. `python main.py` and `pytest` work now.
- These items unblock later phases (real AI responses). None are urgent.
- You may consult ChatGPT before deciding anything. Take your time.

---

## 📋 Good to know — how to REVIEW drafts (your main tool; no setup required)

The system now produces **drafts** and queues them for you. Nothing is ever published.
To view and decide on drafts, open a terminal in the `sportsverse-os` folder and type:

```
python -m review list                       # see drafts waiting for you
python -m review show <id>                   # read one draft in full (incl. the 6 gates)
python -m review approve <id>                # approve the DRAFT only
python -m review revise <id> --notes "..."   # ask for changes (the system drafts a new version)
python -m review reject <id> --reason "..."  # reject and archive, with your reason
python -m review schedule <id>               # approve for scheduled publishing (passes 6 gates)
```

Your four choices: **approve draft only**, **request revision**, **reject**, or
**approve for scheduled publishing**.

> Neither "approve" nor "schedule" posts anything. "schedule" only marks the draft
> `approved_for_scheduled_publish` — cleared for a FUTURE scheduler/publisher that does not
> exist yet and will require its own separate go-ahead from you.

---

## 🧠 Good to know — the Phase 4 "operating core" (no action required)

You can now give the system a plain-English command and it routes the work for you:
```
python -m orchestration "research trending football stories for short-form video"
```
- **Jarvis** turns your words into a task; **Hermes** (the boss agent) decides who handles it.
- Routine work uses **DeepSeek** (cheap); hard reasoning would use **Nemotron** (off by default).
- If a task would cost too much, or asks to publish/email/spend/post, it **stops and asks you**:
  ```
  python -m approval list             # see what's waiting for your OK
  python -m approval approve <id>      # or: reject <id> --reason "..."
  ```
- Nothing is ever published, sent, or spent automatically.

**Optional toggles (only if you want them):**
- Real workflow engine: `pip install langgraph` (auto-detected; not required to run).
- Enable Nemotron for hard reasoning: set `NEMOTRON_ENABLED=true` + `NEMOTRON_API_KEY` +
  `NEMOTRON_BASE_URL` + `NEMOTRON_MODEL` in `.env`. Left off, the system just uses DeepSeek.
- Budget controls: `config/model_budget.json` (monthly cap + per-task approval threshold).

---

## ✅ DONE — Action 1: Core business facts
Provided by you and recorded in `PROJECT_DNA.md`: parent brand **Sportsverse**, main
channel **Platinum Clips**, focus **faceless sports media + affiliate intelligence**,
future brands, and the agent roles (Hermes / OpenClaw / Sentinel / Archivist / Compliance).
- [x] Done

## ✅ DONE — Action 2: Tech stack
Chosen: **Python**. The Phase 1 skeleton is built, runs, and passes tests.
- [x] Done

---

## ✅ DONE — Action 3: Live AI (DeepSeek) is connected and verified

- Provider: **DeepSeek**. `.env` has `LLM_MODE=live`, `LLM_PROVIDER=deepseek`, and your key.
- The `openai` SDK (DeepSeek's client) is installed (v2.38.0).
- **Verified live** on 2026-06-09: a real DeepSeek reply (`is_mock=False`) and a real draft
  through the full pipeline. Nothing was published.
- You can re-check anytime: `python scripts/check_live_llm.py`.

- [x] Done

### You now have a real draft waiting (optional)
A real DeepSeek draft is sitting in your review queue. To see and act on it:
```
python -m review list            # shows the draft + its id
python -m review show <id>        # read it
python -m review approve <id>     # approve the draft, OR:
python -m review schedule <id>    # approve it for scheduling (6 gates)
python -m scheduler propose       # propose a time for approved items (does NOT post)
python -m scheduler confirm <slot_id>
```

---

### (Reference) instructions for switching providers later

**All you need to do is paste your key.** Pick the provider you have a key for:

| Provider | Where to get a key | Line to paste it on (in `.env`) |
|---|---|---|
| Anthropic / Claude | console.anthropic.com → API Keys | `ANTHROPIC_API_KEY=sk-ant-...` |
| OpenAI | platform.openai.com → API keys | `OPENAI_API_KEY=sk-...` |
| DeepSeek | platform.deepseek.com → API keys | `DEEPSEEK_API_KEY=sk-...` |

**Exact steps:**
1. Open the file `sportsverse-os/.env` in a text editor (Notepad is fine).
2. Find the line for your provider (e.g. `ANTHROPIC_API_KEY=`).
3. Paste your key right after the `=` (no spaces, no quotes). Leave the other two blank.
4. Save the file. (`.env` is gitignored — your key is never shared or committed.)
5. Tell the coding agent **which provider** you used (e.g. "I'm using Anthropic").
   - The agent will then install ONLY that one library (`pip install anthropic`, or
     `pip install openai` for OpenAI/DeepSeek) and run a real draft test.
   - It will NOT install libraries you don't need.

> Until the matching library is installed, live calls safely fall back to mock — so nothing
> breaks if you paste the key before telling the agent.

- [ ] Provider used: ______   Key pasted into `.env`: [ ]   Told the agent: [ ]

---

## ⏳ Action 4 — Small details (no accounts needed)

1. **Academy brand name** — what should the future academy brand be called?
2. **Compliance jurisdiction** — which country/region's rules apply to Sportsverse?
   (affects FTC/disclosure wording, etc.)

Just reply to the coding agent with the answers, or write them into `PROJECT_DNA.md`.

- [ ] Academy name: ______
- [ ] Jurisdiction: ______

---

## 🔒 Later (not yet) — Accounts, tokens, domains, VPS

Don't do these yet. The agent will give step-by-step instructions when each is needed:
- Telegram bot token (only if chat automation is used, a later phase)
- Email app password (for owner report emails, a later phase)
- Domain name (when a website is needed)
- VPS login (deployment, a later phase)
- **Phase 4 publishing**: real platform APIs are added ONLY when you explicitly ask, with
  per-item approval. Nothing posts before then.

Live list: `docs/api_keys_needed.md`.

---

## Quick status

| Action | Needed for | Status |
|---|---|---|
| 1 — Business facts | Past foundation | ✅ Done |
| 2 — Tech stack (Python) | Build agents | ✅ Done |
| 3 — DeepSeek live AI | Real AI drafts | ✅ Done & verified |
| 4 — Academy name / jurisdiction | Completeness | ⏳ When convenient |
| Optional — LangGraph / Nemotron toggles | Faster engine / hard reasoning | ⚪ Optional, off by default |
| Later — publishing / VPS deploy | Phase 5 (owner-gated) | 🔒 Not yet (needs your go-ahead) |
