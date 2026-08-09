# Architecture & design notes

## Goal

Collect Warsaw event listings from several public sources and publish them as
subscribable iCal calendars (one per source + a combined one), fully automated
on GitHub Actions.

## Two-stage pipeline

The system is deliberately split into two stages that share only the YAML store
and can be orchestrated independently:

```
                 fetch                          generate
  sources  ─────────────────▶  events/*.yaml  ─────────────────▶  calendars/*.ics
  (web)     scrape + normalize   (durable store)  filter + render     (subscribe)
```

- **fetch** is where all the source-specific fragility lives (HTML/feed
  parsing). It normalizes everything into the `Event` model and upserts into
  YAML. It never decides what is "current" — it just records what exists.
- **generate** is pure and deterministic: read YAML, apply criteria, emit
  `.ics`. It can be re-run any time (e.g. to change the window) without touching
  the network.

Keeping the raw/normalized data in YAML means we can reprocess history — change
the rendering or criteria later and rebuild calendars from stored events.

## Data branch

Generated artifacts (the YAML store and the `.ics` files) are committed to an
orphan branch named `data`, not to the code branch. The Bash wrappers check that
branch out into a git worktree (`.data/`), let the Python entrypoints write into
`events/` and `calendars/` there, and commit + push only on a real diff. This
keeps the code history clean and gives stable `raw.githubusercontent.com` URLs
for subscription.

A single GitHub Actions workflow (`.github/workflows/pipeline.yml`) runs both
stages in order: the fetch stage, then the generate stage. Although it is one
pipeline, the stages remain separately orchestrable — a manual `workflow_dispatch`
run can execute only fetch, only generate, or both (default), via the `stage`
input, and locally each stage has its own script. A `concurrency: data-branch`
group prevents overlapping runs from pushing to `data` at the same time.

## The Event model

`models.Event` is the single normalized shape. Notable choices:

- **Stable UID**: derived from `source + url` (URL is unique per event on all
  current sources). This is intentionally independent of parsed dates, so
  refining date parsing later does not change identities and create duplicates
  in the store. Falls back to `source + title + start` only when no URL exists.
- **Dates**: `start`/`end` are `date` for all-day/multi-day items and
  `datetime` (Europe/Warsaw) when a real time is known. Stored as ISO strings.
- **Upsert by UID** (`storage.upsert`): re-fetching is idempotent; previously
  stored events are retained (history), matching UIDs are refreshed.

## Source specifics

- **expoxxi** — the page embeds `schema.org/Event` JSON-LD, which we read
  directly. Times in the data are a scrape artifact, so trade fairs are treated
  as all-day. These events are months out, so they rarely fall inside the
  14-day generation window.
- **waw4free** — no API; the listing is addressed by a dated URL, so we iterate
  the next 14 days and dedupe. Time is often only in the title, so items are
  all-day. District becomes the location.
- **wola** — the Atom feed lacks event date/location, so for each entry we fetch
  the subpage and parse the date block (after the calendar icon) and address.
  A timed range spanning multiple days (a recurring series shown as one range)
  is converted to an all-day banner to avoid a misleading 40-day timed block.

## Generation criteria

Include an event when it has a title and a start date and it **overlaps**
`[today, today + N]` (default N = 14). Overlap (not "starts within") keeps
long-running exhibitions that are on right now. De-dupe by UID. `N` is
configurable via `--days`.

## Known trade-offs / future work

- HTML parsers are inherently brittle; each source is isolated in its own module
  so a layout change is contained. A parse error on one card/entry is logged and
  skipped rather than aborting the run.
- Recurring events are flattened (no `RRULE`); a multi-day series becomes one
  all-day banner. Per-occurrence expansion could be added later.
- The YAML store grows over time (history is kept). A pruning policy for very
  old events could be added if size becomes a concern.
