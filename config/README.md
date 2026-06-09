# config/

Configuration templates for the system and agents. **No secrets here** — secrets go in
`.env` at the project root.

Once the tech stack is chosen (Phase 1), this holds non-secret runtime config such as:
- system settings (timeouts, log level defaults)
- agent registry / which agents are enabled
- environment-specific config templates (local vs vps)

Convention: ship `*.example` templates here; the real, filled-in config (if it contains
anything sensitive) stays local and gitignored.

> Empty for now — Phase 0 needs no runtime config.
