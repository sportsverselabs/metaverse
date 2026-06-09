"""Sportsverse OS — entry point (Phase 1 skeleton).

Wires the system together and prints a status banner. It deliberately does NOT start
any loops, poll any service, send any message, or publish anything. Running it just
proves the framework imports and assembles cleanly.

Run from the project root:

    python main.py
"""

from __future__ import annotations

from agents.archivist import Archivist
from agents.compliance import Compliance
from agents.hermes import Hermes
from agents.openclaw import OpenClaw
from agents.sentinel import Sentinel
from core.config import load_config
from core.llm_router import LLMRouter
from core.logging_setup import setup_logging
from memory.manager import MemoryManager
from review.store import ReviewStore
from scheduler.store import SchedulerStore
from skills.registry import default_registry


def build_system():
    """Assemble config, services, and the agent org. Returns (hermes, services)."""
    config = load_config()
    logger = setup_logging(config.log_level)
    logger.info("Booting Sportsverse OS (env=%s, phase=%s)", config.env, config.get("phase", 1))

    memory = MemoryManager()
    llm = LLMRouter(config=config)
    registry = default_registry()
    review_store = ReviewStore()
    scheduler_store = SchedulerStore()

    shared = {"config": config, "memory": memory, "llm": llm}
    hermes = Hermes(review_store=review_store, **shared)
    hermes.register(OpenClaw(registry=registry, **shared))
    for agent_cls in (Sentinel, Archivist, Compliance):
        hermes.register(agent_cls(**shared))

    return hermes, {
        "config": config, "logger": logger, "memory": memory, "llm": llm,
        "registry": registry, "review_store": review_store, "scheduler_store": scheduler_store,
    }


def main() -> None:
    hermes, services = build_system()
    log = services["logger"]

    llm = services["llm"]
    registry = services["registry"]
    review_store = services["review_store"]

    log.info("=" * 60)
    log.info("Sportsverse OS - agent org assembled:")
    log.info("  %s  (%s)", hermes.name, hermes.role)
    for name, agent in sorted(hermes.agents.items()):
        log.info("   |- %s  (%s)", name, agent.role)
    log.info("LLM mode: %s (providers: %s)", llm.mode, ", ".join(llm.providers))
    log.info("Whitelisted draft-only skills: %s", ", ".join(registry.names()))
    log.info("Owner-review queue: %d draft(s) awaiting review. Use: python -m review list",
             len(review_store.list_pending()))
    log.info("Scheduler: %d proposed slot(s). Use: python -m scheduler list",
             len(services["scheduler_store"].list(status="proposed")))
    log.info("Safety: approval != publish; scheduling != publish; LLM mode=%s.", llm.mode)
    log.info("No loops started, nothing sent, nothing published. Phase 3 boot.")
    log.info("=" * 60)


if __name__ == "__main__":
    main()
