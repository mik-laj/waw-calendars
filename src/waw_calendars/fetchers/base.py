"""Shared HTTP layer for fetchers (httpx + HTTP/2, retries, throttling)."""

from __future__ import annotations

import logging
import time
from typing import Self

import httpx

log = logging.getLogger("waw_calendars.http")

USER_AGENT = (
    "waw-calendars/0.1 (+https://github.com/; event calendars, contact via repo)"
)

DEFAULT_TIMEOUT = httpx.Timeout(30.0, connect=15.0)


class HttpClient:
    """Thin wrapper over ``httpx.Client`` with retries and gentle throttling.

    ``throttle`` is the minimum spacing (in seconds) between consecutive
    requests — politeness toward servers, especially when crawling many
    subpages (Wola).
    """

    def __init__(self, throttle: float = 0.5, retries: int = 3) -> None:
        self._throttle = throttle
        self._retries = retries
        self._last_request = 0.0
        self._client = httpx.Client(
            http2=True,
            follow_redirects=True,
            timeout=DEFAULT_TIMEOUT,
            headers={"User-Agent": USER_AGENT, "Accept-Language": "pl,en;q=0.8"},
        )

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def close(self) -> None:
        self._client.close()

    def get_text(self, url: str) -> str | None:
        """Fetch a URL and return its text; ``None`` if it fails after retries."""
        for attempt in range(1, self._retries + 1):
            self._wait()
            try:
                resp = self._client.get(url)
                resp.raise_for_status()
                return resp.text
            except (httpx.HTTPError, httpx.StreamError) as exc:
                wait = min(2 ** attempt, 10)
                log.warning(
                    "GET %s failed (attempt %d/%d): %s — waiting %ds",
                    url, attempt, self._retries, exc, wait,
                )
                if attempt < self._retries:
                    time.sleep(wait)
        log.error("GET %s — giving up after %d attempts", url, self._retries)
        return None

    def _wait(self) -> None:
        delta = time.monotonic() - self._last_request
        if delta < self._throttle:
            time.sleep(self._throttle - delta)
        self._last_request = time.monotonic()
