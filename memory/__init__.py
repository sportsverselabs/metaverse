"""Sportsverse OS — memory package.

File-based, portable memory. See ``memory_schema.md`` for the on-disk format.
The :class:`~memory.manager.MemoryManager` reads/writes one markdown file per memory
under ``memory/store/``.
"""

from memory.manager import MemoryManager  # noqa: F401

__all__ = ["MemoryManager"]
