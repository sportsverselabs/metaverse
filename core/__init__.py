"""Sportsverse OS — core framework package.

Cross-cutting framework primitives used by every agent and integration:

- ``paths``          : canonical, portable project paths (relative to this folder)
- ``config``         : load ``.env`` + ``config/settings.json`` into a Config object
- ``logging_setup``  : configure console + rotating-file logging
- ``llm_router``     : route prompts to an LLM provider (skeleton)

Phase 1 skeleton. Infrastructure (paths/config/logging) is functional; the
LLM router is a non-networking stub. See PROJECT_DNA.md for project context.
"""

__all__ = ["paths", "config", "logging_setup", "llm_router"]
__version__ = "0.1.0"
