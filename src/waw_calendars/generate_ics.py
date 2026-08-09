"""Generate stage entrypoint: build iCal (.ics) files from the YAML store.

Usage:
    python -m waw_calendars.generate_ics --in events/ --out calendars/ [--days 14]

Criteria for including an event (per user requirements):
- title present AND start date present,
- the event overlaps the window [today, today + N days]. Overlap (not just
  "start within window") keeps multi-day events that are already running.

Produces one ``<source>.ics`` per source plus a combined ``all.ics``.
"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml
from icalendar import Calendar
from icalendar import Event as IcsEvent

from . import storage
from .models import WARSAW_TZ, Event

log = logging.getLogger("waw_calendars.generate")
TZ = ZoneInfo(WARSAW_TZ)

DEFAULT_DAYS = 14
CONFIG = Path(__file__).resolve().parents[2] / "config" / "sources.yaml"


def load_source_meta() -> dict[str, dict]:
    """Map source id -> its config entry (for calendar display names)."""
    if not CONFIG.exists():
        return {}
    data = yaml.safe_load(CONFIG.read_text(encoding="utf-8")) or {}
    return {s["id"]: s for s in data.get("sources", [])}


def has_required_fields(event: Event) -> bool:
    """Baseline criterion: a usable event needs a title and a start date."""
    return bool(event.title) and event.start_date is not None


def in_window(event: Event, start: date, end: date) -> bool:
    """True if the event has title+date and overlaps [start, end]."""
    if not has_required_fields(event):
        return False
    ev_start = event.start_date
    ev_end = event.end_date or ev_start
    return ev_start <= end and ev_end >= start


def to_ics_event(event: Event) -> IcsEvent:
    """Convert an Event into an icalendar VEVENT component."""
    comp = IcsEvent()
    comp.add("uid", event.uid)
    comp.add("summary", event.title)
    comp.add("dtstamp", datetime.now(TZ))

    if event.all_day or not isinstance(event.start, datetime):
        start = event.start_date
        # DTEND is exclusive for all-day events -> +1 day past the last day.
        end = (event.end_date or start) + timedelta(days=1)
        comp.add("dtstart", start)
        comp.add("dtend", end)
    else:
        comp.add("dtstart", event.start)
        comp.add("dtend", event.end or event.start)

    if event.location:
        comp.add("location", event.location)
    if event.url:
        comp.add("url", event.url)
    if event.description:
        comp.add("description", event.description)
    if event.categories:
        comp.add("categories", event.categories)
    return comp


def build_calendar(name: str, events: list[Event]) -> Calendar:
    cal = Calendar()
    cal.add("prodid", "-//waw-calendars//PL")
    cal.add("version", "2.0")
    cal.add("x-wr-calname", name)
    cal.add("x-wr-timezone", WARSAW_TZ)
    for event in sorted(events, key=lambda e: (e.start_date or date.max, e.title)):
        cal.add_component(to_ics_event(event))
    return cal


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate .ics from YAML store.")
    parser.add_argument("--in", dest="src", type=Path, default=Path("events"))
    parser.add_argument("--out", type=Path, default=Path("calendars"))
    parser.add_argument(
        "--days",
        type=int,
        default=DEFAULT_DAYS,
        help="window length in days (from today)",
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    meta = load_source_meta()
    args.out.mkdir(parents=True, exist_ok=True)

    window_start = datetime.now(TZ).date()
    window_end = window_start + timedelta(days=args.days)
    log.info("window: %s .. %s", window_start, window_end)

    all_events: list[Event] = []
    sources = sorted(meta) or [p.stem for p in args.src.glob("*.yaml")]

    for source in sources:
        stored = storage.load_events(args.src, source)
        # Sources flagged all_events (e.g. trade fairs) export every event with
        # the required fields, ignoring the N-day window.
        if meta.get(source, {}).get("all_events"):
            selected = [e for e in stored if has_required_fields(e)]
        else:
            selected = [e for e in stored if in_window(e, window_start, window_end)]
        # dedup by UID (defensive; store is already deduped)
        selected = list({e.uid: e for e in selected}.values())
        name = meta.get(source, {}).get("name", source)
        cal = build_calendar(name, selected)
        out = args.out / f"{source}.ics"
        out.write_bytes(cal.to_ical())
        log.info("%s: %d/%d events -> %s", source, len(selected), len(stored), out)
        all_events.extend(selected)

    all_events = list({e.uid: e for e in all_events}.values())
    combined = build_calendar("Warszawa — wydarzenia (zbiorczy)", all_events)
    (args.out / "all.ics").write_bytes(combined.to_ical())
    log.info("all.ics: %d events", len(all_events))
    return 0


if __name__ == "__main__":
    sys.exit(main())
