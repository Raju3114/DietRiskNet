"""Timezone-safe UTC datetime helpers.

``datetime.utcnow()`` is deprecated in Python 3.12+.  This module
provides a drop-in replacement that returns the current UTC time as a
*naive* datetime, preserving SQLAlchemy ``DateTime`` column compatibility
(the ORM columns store naive UTC timestamps).
"""

from __future__ import annotations

from datetime import datetime, timezone


def utcnow() -> datetime:
    """Current UTC time as a naive datetime (safe for DB ``DateTime``).

    Equivalent to ``datetime.utcnow()`` but without the deprecation: uses
    ``datetime.now(timezone.utc)`` and strips the tzinfo so column
    comparisons remain consistent.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)
