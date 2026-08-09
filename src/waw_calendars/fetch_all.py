"""Fetch stage entrypoint: run source fetchers and upsert results into YAML.

Usage:
    python -m waw_calendars.fetch_all --out events/ [--source expoxxi ...]

Each source is fetched independently; a failure in one source does not abort the
others. Results are merged into ``events/<source>.yaml`` by UID.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from . import storage
from .fetchers import FETCHERS
from .fetchers.base import HttpClient


def _setup_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fetch events into YAML store.")
    parser.add_argument("--out", type=Path, default=Path("events"),
                        help="output directory for <source>.yaml files")
    parser.add_argument("--source", action="append", dest="sources",
                        choices=sorted(FETCHERS), help="limit to given source(s)")
    parser.add_argument("--throttle", type=float, default=0.5,
                        help="min seconds between HTTP requests")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    _setup_logging(args.verbose)
    log = logging.getLogger("waw_calendars.fetch")

    sources = args.sources or sorted(FETCHERS)
    failures = 0

    with HttpClient(throttle=args.throttle) as client:
        for source in sources:
            log.info("fetching source: %s", source)
            try:
                events = FETCHERS[source](client)
            except Exception:
                log.exception("source %s failed", source)
                failures += 1
                continue
            storage.upsert(args.out, source, events)

    if failures:
        log.error("%d/%d sources failed", failures, len(sources))
    return 1 if failures == len(sources) else 0


if __name__ == "__main__":
    sys.exit(main())
