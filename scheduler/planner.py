"""Time-assignment logic (pure, deterministic, no network).

Proposes posting times for a number of approved items. Default cadence: one item per day at
a fixed hour, starting the day after ``start``. Configurable via ``post_hour`` / ``spacing_days``.
"""

from __future__ import annotations

from datetime import datetime, time, timedelta
from typing import Optional


def propose_times(
    count: int,
    *,
    start: Optional[datetime] = None,
    post_hour: int = 17,
    spacing_days: int = 1,
) -> list[datetime]:
    """Return ``count`` future datetimes.

    First slot is the day after ``start`` at ``post_hour``:00, then every ``spacing_days``.
    Deterministic given ``start`` (pass a fixed value in tests).
    """
    if count <= 0:
        return []
    base = (start or datetime.now()).date()
    first_day = base + timedelta(days=1)
    slot_time = time(hour=max(0, min(23, post_hour)), minute=0)
    return [
        datetime.combine(first_day + timedelta(days=spacing_days * i), slot_time)
        for i in range(count)
    ]
