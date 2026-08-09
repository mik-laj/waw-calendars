# 2026-08-09 — Initial implementation

## What

Bootstrapped the whole project:

- `Event` model with stable URL-based UID and YAML (de)serialization
  (`models.py`), plus an idempotent upsert store keyed by UID (`storage.py`).
- Three source fetchers over a shared httpx/HTTP-2 client (`fetchers/`):
  - `expoxxi` — reads embedded schema.org/Event JSON-LD; trade fairs as all-day.
  - `waw4free` — scrapes dated listing URLs over the next 14 days, deduped.
  - `wola` — Atom feed + per-event subpage parsing for date/location.
- Two entrypoints: `fetch_all.py` (sources → `events/*.yaml`) and
  `generate_ics.py` (`events/*.yaml` → per-source + `all.ics`, criteria =
  title + start date + overlap with a 14-day window).
- Bash orchestration (`scripts/lib.sh`, `fetch.sh`, `generate.sh`) that writes
  artifacts to the orphan `data` branch via a git worktree and commits on diff.
- A single GitHub Actions workflow (`pipeline.yml`) running the fetch stage then
  the generate stage, with a `data-branch` concurrency group. Stages stay
  separately orchestrable via the `stage` dispatch input.
- Docs: `README.md`, `AGENTS.md`, `docs/architecture.md`, this changelog.

## Why

Deliver the requested automated Warsaw event → iCal aggregator with a clean
separation between fetching (fragile, source-specific) and generating
(deterministic, reprocessable), keeping durable history in YAML.

## Notes

- **httpx over requests** (HTTP/2), per user preference.
- UID is URL-based on purpose: refining date parsing must not create duplicate
  entries in the store (learned the hard way when a wola timed-range fix changed
  a date-derived UID and left a stale duplicate).
- A multi-day *timed* range from wola (recurring series shown as one range) is
  collapsed to an all-day banner to avoid a misleading 40-day timed VEVENT.
- Verified end-to-end locally: expoxxi 17, waw4free 520, wola 20 events fetched;
  generation produced valid `.ics` (waw4free 395 / wola 13 in-window; expoxxi 0
  because its fairs are months out — expected).
- Follow-up ideas: RRULE for recurring events, pruning old YAML entries.
