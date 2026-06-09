# reports/

Generated reports and session records.

```
reports/
└─ handoff/
   └─ latest_handoff.md   ← updated at the end of EVERY coding session
```

- **handoff/** — the continuity baton. `latest_handoff.md` lets a new agent resume cold.
  Before a major rewrite, copy it to `handoff_YYYY-MM-DD.md` to keep history.

Future report types (status reports, test reports, build summaries) can live directly
under `reports/` as dated Markdown files.
