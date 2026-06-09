"""Live-LLM connectivity check.

Run AFTER pasting your provider key into .env:

    python scripts/check_live_llm.py

It makes ONE tiny real call through the router and reports which provider answered and
whether it was a real (non-mock) response. If the key is missing it explains that and
falls back to mock — it never crashes and never publishes anything.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.config import load_config
from core.llm_router import LLMRouter
from core.logging_setup import setup_logging


def main() -> int:
    setup_logging("warning")
    config = load_config()
    router = LLMRouter(config=config)

    print("LLM_MODE        :", router.mode)
    print("Pinned provider :", config.get("LLM_PROVIDER") or "(auto-detect)")
    print("Providers wired :", ", ".join(router.providers))
    print("Keys present    :", ", ".join(router.available_providers()))
    print("-" * 50)

    resp = router.complete("Reply with exactly: Sportsverse live check OK.", task_type="general")
    print("answered by     :", resp.provider, f"(model={resp.model})")
    print("is_mock         :", resp.is_mock)
    print("response        :", (resp.text or "").strip()[:200])
    print("-" * 50)

    if router.mode != "live":
        print("NOTE: LLM_MODE is not 'live'. Set LLM_MODE=live in .env for real calls.")
    elif resp.is_mock:
        print("NOTE: Live mode is on but no usable provider key was found, so this fell back to")
        print("      mock (safe). Paste your DEEPSEEK_API_KEY into .env and run this again.")
    else:
        print("SUCCESS: a real provider answered. Live LLM is working.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
