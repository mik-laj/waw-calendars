"""Fetcher for the Wola district (Atom feed + event subpages).

The Atom feed (getRSS) carries no event date or location — only the title, link
and publication date. For each entry we therefore fetch the subpage and parse:
- the date/time from the block following the calendar icon (``div[data-pdf]``),
  format ``DD.MM.YYYY HH:MM - DD.MM.YYYY HH:MM``,
- the location from ``.adres-nazwa``.
Entries with no recognized date still land in YAML (without ``start``) — they are
filtered out later by the generate stage (required-date criterion).
"""

from __future__ import annotations

import logging
import re
from datetime import date, datetime
from zoneinfo import ZoneInfo

import feedparser
from bs4 import BeautifulSoup

from ..models import WARSAW_TZ, Event
from .base import HttpClient

log = logging.getLogger("waw_calendars.wola")

SOURCE = "wola"
TZ = ZoneInfo(WARSAW_TZ)
FEED_URL = (
    "https://wola.um.warszawa.pl/?p_p_id="
    "com_liferay_asset_publisher_web_portlet_AssetPublisherPortlet_INSTANCE_jYdN6Vg9rRjn"
    "&p_p_lifecycle=2&p_p_state=normal&p_p_mode=view&p_p_resource_id=getRSS"
    "&p_p_cacheability=cacheLevelPage"
)

# 'DD.MM.YYYY HH:MM' or bare 'DD.MM.YYYY'
_DT_RE = re.compile(r"(\d{2})\.(\d{2})\.(\d{4})(?:\s+(\d{1,2}):(\d{2}))?")


def _clean_link(url: str) -> str:
    """Strip the ?redirect=... query from a feed entry link."""
    return url.split("?redirect=")[0].split("&redirect=")[0]


def _parse_dt(text: str, want_time: bool) -> date | datetime | None:
    m = _DT_RE.search(text)
    if not m:
        return None
    d, mo, y, hh, mm = m.groups()
    if want_time and hh is not None:
        return datetime(int(y), int(mo), int(d), int(hh), int(mm), tzinfo=TZ)
    return date(int(y), int(mo), int(d))


def _parse_detail(html: str):
    """Return (start, end, all_day, location, description) from a subpage."""
    soup = BeautifulSoup(html, "lxml")

    start = end = None
    all_day = True
    # Date block: div[data-pdf] following the calendar icon.
    for icon in soup.select("span.ico-calendar"):
        container = icon.parent
        div = container.select_one("div[data-pdf]") if container else None
        if not div:
            continue
        text = div.get_text(" ", strip=True)
        # '09.08.2026 18:00 - 09.08.2026 19:30'
        parts = re.split(r"\s*-\s*", text, maxsplit=1)
        has_time = ":" in text
        all_day = not has_time
        start = _parse_dt(parts[0], want_time=has_time)
        if len(parts) > 1:
            end = _parse_dt(parts[1], want_time=has_time)
        if start:
            break

    # A timed range spanning multiple days (recurring series shown as one range)
    # is misleading as a single continuous VEVENT — represent it as an all-day
    # banner across the day range instead.
    if (
        isinstance(start, datetime)
        and isinstance(end, datetime)
        and start.date() != end.date()
    ):
        start, end = start.date(), end.date()
        all_day = True

    location = None
    addr = soup.select_one(".adres-nazwa")
    if addr:
        location = addr.get_text(" ", strip=True).strip(" ,;") or None
    if location:
        location = f"{location}, Warszawa"

    description = None
    body = soup.select_one(".asset-full-content, article .journal-content-article")
    if body:
        text = body.get_text(" ", strip=True)
        description = (text[:800] + "…") if len(text) > 800 else (text or None)

    return start, end or start, all_day, location, description


def fetch(client: HttpClient) -> list[Event]:
    xml = client.get_text(FEED_URL)
    if not xml:
        log.error("wola: no feed")
        return []

    feed = feedparser.parse(xml)
    events: list[Event] = []
    for entry in feed.entries:
        title = (entry.get("title") or "").strip()
        link = _clean_link(entry.get("link") or "")
        if not title or not link:
            continue

        start = end = location = description = None
        all_day = True
        detail = client.get_text(link)
        if detail:
            try:
                start, end, all_day, location, description = _parse_detail(detail)
            except Exception:
                log.exception("wola: subpage parse error %s", link)

        events.append(
            Event(
                source=SOURCE,
                title=title,
                start=start,
                end=end,
                all_day=all_day,
                location=location,
                url=link,
                description=description,
                categories=["Wola"],
            )
        )

    with_date = sum(1 for e in events if e.start is not None)
    log.info("wola: %d entries (%d with a date)", len(events), with_date)
    return events
