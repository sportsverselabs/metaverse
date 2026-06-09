# integrations/

Connectors to external services (messaging, email, sports data, LLM APIs, etc.).
**Built in Phase 3** — nothing here yet.

Rules:
- Each integration reads its credentials from `.env` (never hard-coded).
- Document each integration's required variables in `../docs/api_keys_needed.md`.
- Respect every provider's terms of service and rate limits.
- Prefer free/open-source/low-cost providers (see `../constitution/constitution.md`, Article 6).

Planned layout (example):
```
integrations/
├─ telegram/
├─ email/
└─ sports_data/
```

> Do not add integrations until Phase 3 and until the relevant provider + key are owner-approved.
