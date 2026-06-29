"""Tiny stdlib HTTP helper for publishing adapters.

Tests inject a transport, so this module is only used for real server-side calls
after credentials are present and the owner explicitly publishes an item.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any


@dataclass
class HttpResponse:
    status: int
    data: dict[str, Any] = field(default_factory=dict)
    headers: dict[str, str] = field(default_factory=dict)
    text: str = ""


def default_fetch(method: str, url: str, *, headers: dict | None = None,
                  body: bytes | None = None, timeout: float = 30.0) -> HttpResponse:
    req = urllib.request.Request(url, data=body, headers=headers or {}, method=method.upper())
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            return HttpResponse(resp.status, _json_or_empty(raw), dict(resp.headers.items()), raw)
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        return HttpResponse(exc.code, _json_or_empty(raw), dict(exc.headers.items()), raw)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return HttpResponse(0, {}, {}, f"{type(exc).__name__}: {exc}")


def json_body(data: dict[str, Any]) -> bytes:
    return json.dumps(data, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def form_body(data: dict[str, Any]) -> bytes:
    import urllib.parse

    return urllib.parse.urlencode(data).encode("utf-8")


def _json_or_empty(raw: str) -> dict[str, Any]:
    if not raw.strip():
        return {}
    try:
        parsed = json.loads(raw)
    except ValueError:
        return {}
    return parsed if isinstance(parsed, dict) else {"value": parsed}
