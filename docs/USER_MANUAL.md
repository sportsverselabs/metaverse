# Sportsverse — User Manual (Owner)

This is your day-to-day guide. Nothing publishes without your approval.

## The big idea
You give a command → the system researches/writes/drafts → you review and approve → it gets
scheduled. You are always the final step before anything could go public.

## Run a command (Jarvis)
```
python -m orchestration "research trending NBA storylines for short-form video"
python -m orchestration "draft a punchy caption for a buzzer-beater clip"
python -m orchestration "design a 4-week content plan"        # complex → Nemotron if enabled
```

## Review and decide on drafts
```
python -m review list                          # see drafts waiting
python -m review show <id>                      # read one in full
python -m review approve <id>                   # approve the DRAFT only
python -m review revise <id> --notes "..."      # ask for changes
python -m review reject  <id> --reason "..."    # reject + archive
python -m review schedule <id>                  # approve for scheduled publish (6 gates)
```

## Schedule approved items (proposes times — never posts)
```
python -m scheduler propose
python -m scheduler list
python -m scheduler confirm <slot_id>
```

## Approvals for risky actions (publish/spend/etc.)
```
python -m approval list
python -m approval approve <id>
python -m approval reject  <id> --reason "..."
```

## Telegram control
Set `TELEGRAM_BOT_TOKEN` in `.env`, run `python scripts/run_telegram.py`, then in Telegram:
`/status` `/today` `/weekly` `/approvals` `/approve <id>` `/reject <id> <reason>` `/edit <id> <notes>`
`/drafts` `/publish_queue` `/cost` `/security` `/backup` `/deploy_status` `/help`

## Dashboard
```
python -m dashboard            # then open http://127.0.0.1:8787
```
Shows status, pending approvals, drafts, content calendar, agent activity, cost, and your to-do list.

## Editing videos
The video agent drafts concepts/scripts/metadata. Edit the actual video in **CapCut** (free; great
for TikTok/Reels/Shorts), export 9:16 ≤60s, then upload the edited file back through the approval
flow (`upload_edited_version`). After upload it becomes the approved version pending final confirm.

## Daily routine (suggested)
1. Read the morning `/today` report. 2. Clear pending approvals. 3. Give 1–2 new commands.
4. Confirm schedule slots. 5. Check `/security` weekly.
