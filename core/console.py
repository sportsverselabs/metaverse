"""Console helpers.

Model output (and real LLM drafts) often contain non-ASCII characters (emojis, em-dashes).
On some platforms the default console encoding (e.g. Windows cp1252) cannot encode them and
``print`` raises UnicodeEncodeError. Call :func:`enable_utf8_console` at the start of any CLI
``main`` to make stdout/stderr robust (UTF-8, replacing anything unencodable).
"""

from __future__ import annotations

import sys


def enable_utf8_console() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")  # Python 3.7+
        except (AttributeError, ValueError):
            pass
