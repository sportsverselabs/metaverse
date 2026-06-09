# Approval Rules

> When a coding agent must STOP and ask the owner — and when it must NOT.
> Companion to [`constitution.md`](constitution.md). Last updated: 2026-06-08

---

## Default: act autonomously

Do all tasks you can without asking. Do not ask unnecessary questions.
Document what you did so the owner can review later.

---

## STOP and ask the owner ONLY when:

1. **An account must be created** (e.g. signing up for a service).
2. **A paid tool / paid plan decision** is required (anything that costs money).
3. **An API key or secret is needed** (only the owner can obtain it).
4. **A legal or business decision** is required.
5. **A security-sensitive choice** is needed.
6. **Multiple viable tools exist** and the best choice is not obvious.

When you stop for one of these:
- Write the decision into `OWNER_ACTION_REQUIRED.md` with **beginner-friendly steps**.
- If it's a tool choice, list the options with clear pros/cons and a recommended default.
- Note that the owner may consult ChatGPT before deciding.

---

## Beginner-friendly step format (use this for owner actions)

```
1. Go to <website>
2. Click <button>
3. Copy <value>
4. Paste <value> into <file/field>
5. Confirm completion (tick the checkbox)
```

---

## Do NOT ask when:

- The task is purely technical and reversible.
- A sensible low-cost/open-source default exists (pick it, document it).
- It's documentation, scaffolding, refactoring, or organizing files.
- The answer is already recorded in `PROJECT_DNA.md` or these constitution files.

---

## Tie-breaker for tool choices

If you must choose a tool and none of the "STOP" conditions strictly apply
(e.g. all candidates are free/open-source), pick using the Article 6 priority
order in `constitution.md` and document the choice in `PROJECT_DNA.md` Section 11.
Only escalate if the options are genuinely close and the decision is hard to reverse.
