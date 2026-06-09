"""Smoke test: the whole skeleton imports and the system assembles offline."""


def test_packages_import():
    import core.config          # noqa: F401
    import core.logging_setup   # noqa: F401
    import core.llm_router      # noqa: F401
    import agents.base          # noqa: F401
    import agents.hermes        # noqa: F401
    import agents.openclaw      # noqa: F401
    import agents.sentinel      # noqa: F401
    import agents.archivist     # noqa: F401
    import agents.compliance    # noqa: F401
    import memory.manager       # noqa: F401
    import integrations.telegram_interface  # noqa: F401
    import integrations.email_report        # noqa: F401
    import workflows.runner     # noqa: F401


def test_build_system_assembles():
    from main import build_system

    hermes, services = build_system()
    assert hermes.name == "hermes"
    # All four sub-agents are registered under Hermes.
    assert set(hermes.agents) == {"openclaw", "sentinel", "archivist", "compliance"}
    assert services["config"] is not None
