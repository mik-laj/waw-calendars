# 2026-08-09 — Always export all trade-fair events

## What

Added an `all_events: true` flag on a source in `config/sources.yaml`. When set,
the generate stage exports every event that has a title and start date for that
source, bypassing the N-day window. Enabled it for `expoxxi`.

## Why

Trade fairs are scheduled months ahead, so the 14-day window left `expoxxi.ics`
empty. The user wants all fair events always available.

## Notes

- Implemented via `has_required_fields()` in `generate_ics.py`; windowed sources
  keep the overlap check. `all.ics` therefore also includes all fair events.
- Verified locally: `expoxxi.ics` went from 0 to 17 VEVENT; `all.ics` 425.
