from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

from .config import settings

TZ = ZoneInfo(settings.timezone)

# Lets tests and the demo "run reminders as of <date>" control fix "today".
_today_override: date | None = None


def now() -> datetime:
    """Local wall-clock time without tzinfo (stored as-is in the database)."""
    return datetime.now(TZ).replace(tzinfo=None, microsecond=0)


def today() -> date:
    return _today_override or datetime.now(TZ).date()


def set_today(value: date | None) -> None:
    global _today_override
    _today_override = value
