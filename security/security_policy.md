# Security Policy (Baseline)

> Minimum security practices for Sportsverse OS. Grows with the project.
> Last updated: 2026-06-08

---

## 1. Secrets

- Secrets live **only** in a local `.env` file. Never in code, docs, or git.
- Only `.env.example` (placeholders) is shared/committed.
- `.env` is listed in `.gitignore`.
- Never log, print, or echo secret values.
- If a secret is exposed: rotate it immediately, then record the incident in §6 below.

## 2. Access

- The owner controls all accounts and credentials.
- Agents only get the credentials they explicitly need, via `.env` variables mapped in their definition.
- No agent stores credentials in its own memory.

## 3. Data

- Do not collect or store personal data without an owner-approved reason and a documented, secure location.
- Keep private/generated data out of git (`memory/store/`, `logs/` are gitignored).
- Only use sports data/media/content the owner has the right to use.

## 4. Third parties

- Respect every external service's terms of service and rate limits.
- Prefer providers with clear docs and reasonable privacy terms.
- Do not give third-party tools more access than they need.

## 5. Safe-action rule

Agents must NOT, without explicit owner approval:
- spend money,
- send external messages or emails,
- publish or post content publicly,
- take any legally or financially binding action,
- delete or overwrite owner data they did not create.

## 6. Incident log

Record any security issue here (date, what happened, action taken).

| Date | Incident | Action taken |
|---|---|---|
| — | (none yet) | — |

## 7. Backups

- Keep at least one backup of the project off its live machine (external drive or local copy).
- Back up `.env` separately and securely; never store it alongside public code.
- Test that a backup can actually be restored (see `deployment/vps_setup_guide.md` §8).

## 8. Review

Revisit this policy whenever: a new integration is added, a new key is introduced,
or the project moves to a new environment (e.g. VPS).
