# agents/

One folder per agent (created in Phase 1+). Each agent folder contains:

```
<agent_name>/
├─ agent.md        ← definition: role, permissions, limits, escalation, tools
├─ config.example  ← config template (NO secrets)
└─ memory/         ← agent-specific memory (data gitignored)
```

**Nothing is built here yet** — Phase 0 is foundation only.

Planned first agents: **Hermes** (coordinator) and **OpenClaw** (under Hermes).
See `../architecture/agent_architecture.md` for the definition template and rules.

> Do not create agent folders until the tech stack is chosen
> (`../OWNER_ACTION_REQUIRED.md`, Action 2) and Phase 1 begins.
