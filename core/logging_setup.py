"""Logging configuration.

Sets up a console handler plus a rotating file handler that writes to ``logs/``.
Standard library only. Named ``logging_setup`` (not ``logging``) so it never shadows
the stdlib ``logging`` module.

SECURITY: never log secrets (API keys, tokens, passwords). Helpers in this project
read secrets via ``Config.secret(...)`` and must not pass them to the logger.
"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from typing import Optional

from core import paths

_LEVELS = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warn": logging.WARNING,
    "warning": logging.WARNING,
    "error": logging.ERROR,
}

_CONFIGURED = False
ROOT_LOGGER_NAME = "sportsverse"


def setup_logging(level: Optional[str] = None) -> logging.Logger:
    """Configure and return the project root logger (``sportsverse``).

    Idempotent: calling it more than once will not add duplicate handlers.
    ``level`` is a string like ``"info"``/``"debug"``; defaults to INFO.
    """
    global _CONFIGURED
    logger = logging.getLogger(ROOT_LOGGER_NAME)
    log_level = _LEVELS.get((level or "info").lower(), logging.INFO)
    logger.setLevel(log_level)

    if _CONFIGURED:
        logger.setLevel(log_level)
        return logger

    fmt = logging.Formatter(
        fmt="%(asctime)s  %(levelname)-7s  %(name)s  %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console = logging.StreamHandler()
    console.setFormatter(fmt)
    logger.addHandler(console)

    try:
        paths.ensure_runtime_dirs()
        file_handler = RotatingFileHandler(
            paths.LOG_FILE, maxBytes=1_000_000, backupCount=5, encoding="utf-8"
        )
        file_handler.setFormatter(fmt)
        logger.addHandler(file_handler)
    except OSError:
        # If the log directory is not writable (e.g. read-only mount), keep console only.
        logger.warning("File logging disabled: could not open %s", paths.LOG_FILE)

    logger.propagate = False
    _CONFIGURED = True
    logger.debug("Logging initialised at level %s", logging.getLevelName(log_level))
    return logger


def get_logger(name: str) -> logging.Logger:
    """Return a child logger under the project root (e.g. ``sportsverse.agent.hermes``)."""
    return logging.getLogger(f"{ROOT_LOGGER_NAME}.{name}")
