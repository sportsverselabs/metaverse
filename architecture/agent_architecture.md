# Agent Architecture

> How agents are structured, defined, and governed in Sportsverse OS.
> Scaffold — agent runtime not built yet (Phase 1+). Last updated: 2026-06-08

---

## 1. Chain of command

```
Owner (human)
 └─ Hermes              top coordinator agent
     ├─ OpenClaw        sub-agent, operates UNDER Hermes   [LOCKED]
     ├─ [Agent 2]       TBD
     └─ [Agent N]       TBD
```

- **Owner** has final authority and approval power.
- **Hermes** coordinates and delegates. Acts on the owner's behalf within defined limits.
- **OpenClaw** is subordinate to Hermes; only acts on tasks Hermes delegates.
- New agents are added under Hermes (or under another agent) with an owner-approved definition.

## 2. One folder per agent (planned layout)

When agents are built (Phase 1+), each gets its own folder so the system stays portable
and each agent is self-contained:

```
agents/
├─ hermes/
│  ├─ agent.md          ← definition (role, permissions, limits)   [human-readable]
│  ├─ config.example    ← config template (no secrets)
│  └─ memory/           ← agent-specific memory (gitignored data)
├─ openclaw/
│  ├─ agent.md
│  ├─ config.example
│  └─ memory/
└─ _template/
   └─ agent.md          ← copy this to define a new agent
```

> Note: these folders are **not created yet** — they belong to Phase 1.
> This document describes the intended shape so the next agent builds it consistently.

## 3. Agent definition template

Every agent's `agent.md` must answer:

| Field | Meaning |
|---|---|
| **Name** | Agent's name (e.g. Hermes) |
| **Reports to** | Owner / Hermes / other agent |
| **Purpose** | One sentence: why this agent exists |
| **Can do** | Explicit list of allowed actions |
| **Must never do** | Explicit hard limits |
| **Escalates when** | Conditions that require asking up the chain |
| **Tools/APIs needed** | What it depends on (mapped to `.env` keys) |
| **Memory** | What it remembers and where |

## 4. Permissions model

1. Agents only have permissions granted in their `agent.md`.
2. No agent grants itself new permissions.
3. Anything matching the Approval Rules (`constitution/approval_rules.md`) escalates:
   sub-agent → Hermes → owner.
4. No agent spends money, publishes externally, or takes binding actions without owner approval.

## 5. Hermes (placeholder definition)

- **Reports to:** Owner
- **Purpose:** `[TBD — OWNER INPUT NEEDED]` — coordinate Sportsverse OS work and delegate to sub-agents.
- **Can do:** `[TBD]`
- **Must never do:** spend money / publish / take binding actions without owner approval.
- **Escalates when:** any Approval-Rule condition is hit.

## 6. OpenClaw (placeholder definition)  [position LOCKED: under Hermes]

- **Reports to:** Hermes
- **Purpose:** `[TBD — OWNER INPUT NEEDED]`
- **Can do:** only tasks explicitly delegated by Hermes (until defined otherwise).
- **Must never do:** act outside delegated tasks; bypass Hermes; anything in "Must never do" for the system.
- **Escalates when:** task is ambiguous or hits an Approval-Rule condition → escalate to Hermes.

## 7. Communication (to be designed in Phase 1)

How agents pass messages/tasks to each other is **not yet decided** and depends on the
chosen runtime. Keep it simple, portable, and inspectable (e.g. structured messages
stored under the project, not in an external proprietary queue) unless the owner approves otherwise.
