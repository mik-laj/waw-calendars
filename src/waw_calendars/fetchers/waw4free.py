"""Fetcher for waw4free.pl — free events in Warsaw.

The listing is addressed by a dated URL (``warszawa-wydarzenia-YYYY-M-D``), so we
iterate over the next 14 days. From each ``.box`` card we read the title, link,
categories and ``.box-data`` (date range + district). The time is often only in
the title, so events are treated as all-day.
"""

from __future__ import annotations

import logging
import re
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup

from ..models import WARSAW_TZ, Event
from .base import HttpClient

log = logging.getLogger("waw_calendars.waw4free")

SOURCE = "waw4free"
BASE = "https://waw4free.pl/"
LISTING = "https://waw4free.pl/warszawa-wydarzenia-{y}-{m}-{d}"
WINDOW_DAYS = 14
TZ = ZoneInfo(WARSAW_TZ)

_DATE_RE = re.compile(r"(\d{2})\.(\d{2})\.(\d{4})")


def _parse_date(text: str) -> date | None:
    m = _DATE_RE.search(text)
    if not m:
        return None
    d, mo, y = (int(x) for x in m.groups())
    try:
        return date(y, mo, d)
    except ValueError:
        return None


def _parse_card(box) -> Event | None:
    """Parse a single ``.box`` listing card into an Event."""
    title_a = box.select_one(".box-title a")
    if not title_a:
        return None
    title = title_a.get_text(strip=True)
    href = title_a.get("href", "").strip()
    if not title or not href:
        return None
    url = href if href.startswith("http") else BASE + href.lstrip("/")

    categories = [
        a.get_text(strip=True)
        for a in box.select(".box-category a")
        if a.get_text(strip=True)
    ]

    start = end = None
    location = None
    data_div = box.select_one(".box-data")
    if data_div:
        # dates: first and (optionally) last in document order
        dates = [
            d for d in (_parse_date(a.get_text()) for a in data_div.select("a")) if d
        ]
        if dates:
            start = dates[0]
            end = dates[-1]
        # district: link whose title reads "... w dzielnicy X"
        for a in data_div.select("a"):
            if "dzielnic" in (a.get("title") or "").lower():
                location = a.get_text(strip=True)
                break

    if location:
        location = f"{location}, Warszawa"

    return Event(
        source=SOURCE,
        title=title,
        start=start,
        end=end or start,
        all_day=True,
        location=location,
        url=url,
        description=None,
        categories=categories,
    )


def fetch(client: HttpClient, today: date | None = None) -> list[Event]:
    today = today or datetime.now(TZ).date()
    by_uid: dict[str, Event] = {}

    for offset in range(WINDOW_DAYS):
        day = today + timedelta(days=offset)
        url = LISTING.format(y=day.year, m=day.month, d=day.day)
        html = client.get_text(url)
        if not html:
            continue
        soup = BeautifulSoup(html, "lxml")
        for box in soup.select(".box"):
            if not box.select_one(".box-title"):
                continue
            try:
                event = _parse_card(box)
            except Exception:
                log.exception("waw4free: card parse error (%s)", url)
                continue
            if event:
                by_uid[event.uid] = event

    events = list(by_uid.values())
    log.info("waw4free: %d unique events (%d-day window)", len(events), WINDOW_DAYS)
    return events
