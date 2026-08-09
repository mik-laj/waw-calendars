"""Fetcher for EXPO XXI Warszawa (https://expoxxi.pl/events_pl/).

The site uses the EventON plugin and embeds event data as JSON-LD
(schema.org/Event). That is the cleanest source, so we read it directly.
Times in the data are an artifact (the fetch timestamp), so trade fairs are
treated as all-day events (date part only).
"""

from __future__ import annotations

import json
import logging
import re
from datetime import date

from bs4 import BeautifulSoup

from ..models import Event
from .base import HttpClient

log = logging.getLogger("waw_calendars.expoxxi")

SOURCE = "expoxxi"
URL = "https://expoxxi.pl/events_pl/"
LOCATION = "EXPO XXI Warszawa, ul. Prądzyńskiego 12/14, Warszawa"

_LD_RE = re.compile(
    r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', re.DOTALL
)


def _parse_date(value: str | None) -> date | None:
    """schema.org date, e.g. '2026-9-3T17:02+0:00' -> date(2026, 9, 3)."""
    if not value:
        return None
    m = re.match(r"(\d{4})-(\d{1,2})-(\d{1,2})", value)
    if not m:
        return None
    y, mo, d = (int(x) for x in m.groups())
    try:
        return date(y, mo, d)
    except ValueError:
        return None


def _clean_description(value: str | None) -> str | None:
    """Strip HTML/WordPress-block markup from a JSON-LD description."""
    if not isinstance(value, str) or not value.strip():
        return None
    text = BeautifulSoup(value, "lxml").get_text(" ", strip=True)
    text = " ".join(text.split())
    if not text:
        return None
    return (text[:800] + "…") if len(text) > 800 else text


def _iter_ld_events(html: str):
    """Yield schema.org Event dicts embedded as JSON-LD in the page."""
    for block in _LD_RE.findall(html):
        try:
            data = json.loads(block)
        except json.JSONDecodeError:
            continue
        for item in data if isinstance(data, list) else [data]:
            if isinstance(item, dict) and item.get("@type") == "Event":
                yield item


def fetch(client: HttpClient) -> list[Event]:
    html = client.get_text(URL)
    if not html:
        log.error("expoxxi: no page content")
        return []

    events: list[Event] = []
    for item in _iter_ld_events(html):
        title = (item.get("name") or "").strip()
        if not title:
            continue
        start = _parse_date(item.get("startDate"))
        end = _parse_date(item.get("endDate")) or start
        loc = item.get("location")
        if isinstance(loc, dict) and loc.get("name"):
            location = loc["name"]
        else:
            location = LOCATION
        desc = _clean_description(item.get("description"))
        events.append(
            Event(
                source=SOURCE,
                title=title,
                start=start,
                end=end,
                all_day=True,
                location=location,
                url=item.get("url"),
                description=desc,
                categories=["targi"],
            )
        )
    log.info("expoxxi: %d events", len(events))
    return events
