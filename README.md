# waw-calendars

Aggregates Warsaw event listings from several public sources and publishes them
as subscribable **iCal (`.ics`)** calendars — one per source plus a combined one.

Everything runs on GitHub Actions. There are two independent stages so they can
be orchestrated separately:

1. **fetch** — scrape sources into a per-source **YAML** store (durable working
   history that can be reprocessed later).
2. **generate** — turn the YAML into `.ics`, keeping only events that meet the
   criteria (see below).

Generated artifacts live on a separate orphan branch, **`data`**, so the code
branch stays clean.

## Sources

| id         | source                              | how                                             |
|------------|-------------------------------------|-------------------------------------------------|
| `expoxxi`  | expoxxi.pl/events_pl                | JSON-LD (schema.org/Event) embedded in the page |
| `waw4free` | waw4free.pl                         | HTML scrape, dated URLs over the next 14 days   |
| `wola`     | wola.um.warszawa.pl (getRSS)        | Atom feed + per-event subpage for date/location |

## Generation criteria

An event is written to a calendar when it has a **title** and a **start date**,
and it **overlaps the window** `[today, today + N days]` (default `N = 14`).
Overlap (rather than "start within window") keeps multi-day events that are
already running. Events are de-duplicated by a stable UID.

> Note: `expoxxi` events are trade fairs scheduled months ahead, so its calendar
> is often empty under the default 14-day window — that is expected.

## Subscribing

After the pipeline has run at least once, the calendars are available as raw
files on the `data` branch:

```
https://raw.githubusercontent.com/mik-laj/waw-calendars/data/calendars/all.ics
https://raw.githubusercontent.com/mik-laj/waw-calendars/data/calendars/expoxxi.ics
https://raw.githubusercontent.com/mik-laj/waw-calendars/data/calendars/waw4free.ics
https://raw.githubusercontent.com/mik-laj/waw-calendars/data/calendars/wola.ics
```

Add the URL as a "subscribe by URL" calendar in Google/Apple Calendar.

## Local development

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
export PYTHONPATH=src

# fetch -> events/*.yaml
python -m waw_calendars.fetch_all --out events

# generate -> calendars/*.ics
python -m waw_calendars.generate_ics --in events --out calendars --days 14
```

Useful flags: `--source <id>` (fetch one source), `-v` (debug logging),
`--throttle <seconds>` (fetch politeness delay).

The `scripts/fetch.sh` and `scripts/generate.sh` wrappers do the same but read
and write the `data` branch via a git worktree, then commit and push. A single
GitHub Actions workflow (`.github/workflows/pipeline.yml`) runs the fetch stage
then the generate stage; a manual run can execute just one stage via the `stage`
input.

## Layout

```
config/sources.yaml            # source definitions + calendar names
src/waw_calendars/
  models.py                    # Event model, stable UID, YAML (de)serialization
  storage.py                   # YAML load/save + idempotent upsert by UID
  fetchers/{base,expoxxi,waw4free,wola}.py
  fetch_all.py                 # fetch entrypoint
  generate_ics.py              # generate entrypoint
scripts/{lib,fetch,generate}.sh
.github/workflows/pipeline.yml   # single workflow, fetch stage then generate stage
docs/                          # architecture & design notes
changelog/                     # dated notes on what changed and why
```

See [`docs/architecture.md`](docs/architecture.md) for the design and
[`AGENTS.md`](AGENTS.md) for contributor/agent conventions.
