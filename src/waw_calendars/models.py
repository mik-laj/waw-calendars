"""Event data model and YAML (de)serialization.

Events are stored in YAML using plain types (ISO strings for dates) so the file
stays human-readable and stable across versions. In memory we work with
``datetime.date`` / ``datetime.datetime`` — see :meth:`Event.start_date`.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Any

WARSAW_TZ = "Europe/Warsaw"


def _parse_dt(value: Any) -> date | datetime | None:
    """Parse an ISO string into a ``date`` (date-only) or ``datetime``."""
    if value is None or value == "":
        return None
    if isinstance(value, (date, datetime)):
        return value
    s = str(value).strip()
    # Date only: YYYY-MM-DD
    if len(s) == 10 and s.count("-") == 2:
        return date.fromisoformat(s)
    return datetime.fromisoformat(s)


def _fmt_dt(value: date | datetime | None) -> str | None:
    """Format a ``date``/``datetime`` as an ISO string for YAML storage."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    return value.isoformat()  # date -> 'YYYY-MM-DD'


@dataclass
class Event:
    """A single event from any source."""

    source: str
    title: str
    start: date | datetime | None = None
    end: date | datetime | None = None
    all_day: bool = False
    location: str | None = None
    url: str | None = None
    description: str | None = None
    categories: list[str] = field(default_factory=list)
    fetched_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.fetched_at is None:
            self.fetched_at = datetime.now(timezone.utc)

    @property
    def uid(self) -> str:
        """Stable, deterministic identifier (idempotent fetch + dedup).

        Prefer the event URL as the identity key — it is unique per event on all
        supported sources and stays stable even if date parsing is later
        refined. Only when there is no URL do we fall back to title + start.
        """
        if self.url:
            key = f"{self.source}|{self.url.strip().lower()}"
        else:
            key = f"{self.source}|{self.title.strip().lower()}|{_fmt_dt(self.start) or ''}"
        digest = hashlib.sha1(key.encode("utf-8")).hexdigest()[:16]
        return f"{digest}@waw-calendars"

    @property
    def start_date(self) -> date | None:
        """Start date as ``date`` (used for window filtering)."""
        if self.start is None:
            return None
        return self.start.date() if isinstance(self.start, datetime) else self.start

    @property
    def end_date(self) -> date | None:
        """End date as ``date`` (falls back to the start date)."""
        end = self.end
        if end is None:
            return self.start_date
        return end.date() if isinstance(end, datetime) else end

    # -- serialization ------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        return {
            "uid": self.uid,
            "source": self.source,
            "title": self.title,
            "start": _fmt_dt(self.start),
            "end": _fmt_dt(self.end),
            "all_day": self.all_day,
            "location": self.location,
            "url": self.url,
            "description": self.description,
            "categories": list(self.categories),
            "fetched_at": _fmt_dt(self.fetched_at),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Event:
        fetched = _parse_dt(data.get("fetched_at"))
        return cls(
            source=data["source"],
            title=data["title"],
            start=_parse_dt(data.get("start")),
            end=_parse_dt(data.get("end")),
            all_day=bool(data.get("all_day", False)),
            location=data.get("location"),
            url=data.get("url"),
            description=data.get("description"),
            categories=list(data.get("categories") or []),
            fetched_at=fetched if isinstance(fetched, datetime) else None,
        )
