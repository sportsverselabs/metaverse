"""Deployment agent — guides VPS deployment. Produces checklists; never deploys silently.

It asks the owner (in plain English) for the exact credentials it needs, produces a step-by-step
checklist, and tracks deploy status. The actual deploy is run by the owner via
``scripts/deploy_vps.sh`` (which prompts for confirmation). No production change without approval.
"""

from __future__ import annotations

from core.logging_setup import get_logger

REQUIRED_CREDENTIALS = [
    ("VPS_HOST", "Your Hostinger VPS IP address (e.g. 203.0.113.10)"),
    ("VPS_USER", "Your VPS username (often 'root' or a sudo user)"),
    ("SSH access", "How you log in: SSH key (preferred) or password"),
    ("DEEPSEEK_API_KEY", "Your DeepSeek API key (already set locally)"),
    ("TELEGRAM_BOT_TOKEN", "Telegram bot token from @BotFather"),
    ("TELEGRAM_CHAT_ID", "Your Telegram chat id (the bot will tell you, or use @userinfobot)"),
    ("GITHUB repo URL", "Where to back up the code (e.g. https://github.com/you/sportverse.git)"),
    ("DNS access", "Hostinger domain/DNS panel access to point sportsversenews.com to the VPS"),
]

CHECKLIST = [
    "1. Back up code to GitHub (scripts/backup_github.sh) — secrets stay out via .gitignore.",
    "2. Create/confirm the Hostinger VPS; note its IP and your SSH login.",
    "3. SSH in; install Python 3 + git (see docs/DEPLOYMENT_GUIDE.md).",
    "4. Clone the repo (or scp the folder) onto the VPS.",
    "5. Create .env on the VPS from .env.example; paste keys (never commit .env).",
    "6. Run scripts/healthcheck.sh to verify the app imports and boots.",
    "7. Set up a process manager (systemd service) so it runs continuously.",
    "8. (Optional) reverse proxy (nginx) + SSL (certbot) for the dashboard/website.",
    "9. Point sportsversenews.com DNS at the VPS IP (A records).",
    "10. Set the Telegram bot token; run the bot; send /status to confirm control.",
    "11. Owner confirms website + dashboard are live. Deployment complete.",
]


class DeploymentAgent:
    name = "deployment_agent"

    def __init__(self, logger=None) -> None:
        self.log = logger or get_logger("agent.deployment")

    def required_credentials(self) -> list:
        return list(REQUIRED_CREDENTIALS)

    def checklist(self) -> list:
        return list(CHECKLIST)

    def next_missing_credential(self, have: set) -> str | None:
        """Return the next credential to ask the owner for, one at a time."""
        for key, prompt in REQUIRED_CREDENTIALS:
            if key not in have:
                return f"I need: {prompt}  (sets {key})"
        return None

    def report(self) -> str:
        return "VPS deployment checklist:\n" + "\n".join(f"  {step}" for step in self.checklist())
