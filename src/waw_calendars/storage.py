"""YAML persistence for events, with idempotent upsert by UID.

Each source is stored in its own file ``<dir>/<source>.yaml`` as a mapping with
an ``events`` list. Fetching merges new events into the existing file keyed by
:pyattr:`Event.uid`, so re-runs are idempotent and history is preserved
(past events are kept for later reprocessing).
"""

from __future__ import annotations

import logging
from pathlib import Path

import yaml

from .models import Event

log = logging.getLogger("waw_calendars.storage")


def _path(events_dir: Path, source: str) -> Path:
    return events_dir / f"{source}.yaml"


def load_events(events_dir: Path, source: str) -> list[Event]:
    """Load events for a source; empty list if the file does not exist."""
    path = _path(events_dir, source)
    if not path.exists():
        return []
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return [Event.from_dict(item) for item in data.get("events", [])]


def save_events(events_dir: Path, source: str, events: list[Event]) -> Path:
    """Write events for a source, sorted by (start, title) for stable diffs."""
    events_dir.mkdir(parents=True, exist_ok=True)
    path = _path(events_dir, source)

    def sort_key(e: Event):
        return (e.start_date is None, e.start_date or "", e.title.lower())

    payload = {
        "source": source,
        "count": len(events),
        "events": [e.to_dict() for e in sorted(events, key=sort_key)],
    }
    path.write_text(
        yaml.safe_dump(payload, allow_unicode=True, sort_keys=False, width=100),
        encoding="utf-8",
    )
    return path


def upsert(events_dir: Path, source: str, fresh: list[Event]) -> tuple[int, int]:
    """Merge freshly fetched events into stored ones by UID.

    Newer entries overwrite matching UIDs; previously stored events without a
    match are retained. Returns ``(total, added)``.
    """
    existing = {e.uid: e for e in load_events(events_dir, source)}
    before = len(existing)
    for event in fresh:
        existing[event.uid] = event
    merged = list(existing.values())
    save_events(events_dir, source, merged)
    added = len(merged) - before
    log.info("%s: stored %d events (+%d new/updated)", source, len(merged), added)
    return len(merged), added
