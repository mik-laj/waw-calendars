# AGENTS.md

Conventions for anyone (human or AI agent) working in this repository.

## Language

- **Code docstrings, inline comments, and all documentation are in English.**
- Repository content (README, `docs/`, `changelog/`, this file) is in English.

## Project shape

- Python does the parsing/rendering; Bash orchestrates and talks to git.
- Two independent stages: **fetch** (sources → `events/*.yaml`) and **generate**
  (`events/*.yaml` → `calendars/*.ics`). Do not couple them.
- Generated artifacts live on the orphan **`data`** branch, never on the code
  branch. `events/` and `calendars/` are git-ignored on the code branch.

## HTTP

- Use **httpx** with HTTP/2 (`httpx[http2]`); do not add `requests`.
- All network access goes through `fetchers/base.HttpClient` (retries + gentle
  throttling). Be polite: keep a throttle delay when crawling many subpages.

## Adding a source

1. Add a module under `src/waw_calendars/fetchers/` exposing
   `fetch(client) -> list[Event]`.
2. Register it in `fetchers/__init__.py:FETCHERS` and in `config/sources.yaml`.
3. Normalize into `models.Event`. Give every event a stable `url` so the UID is
   stable. Prefer structured data (JSON-LD, feeds) over scraping when available.
4. Make parsing resilient: a bad single item is logged and skipped, never fatal.

## Conventions

- Keep the `Event` UID independent of parsed dates (URL-based) so refining a
  parser does not spawn duplicates in the store.
- Times are Europe/Warsaw; all-day items use `date`, timed items use `datetime`.
- Prefer standard-library typing syntax (`X | None`); the code targets 3.12+.

## Linting / pre-commit

- Run `pre-commit install` once; hooks run on every commit. Config lives in
  `.pre-commit-config.yaml`, ruff settings in `pyproject.toml`. The same hooks
  run in CI (`.github/workflows/pre-commit.yml`) on pushes/PRs to `main`.
- Hooks: ruff (lint + `--fix`), ruff-format, shellcheck (Docker), hadolint
  (Docker, Dockerfile), YAML/TOML checks, GitHub-workflow schema validation,
  `detect-private-key`, shebang/executable consistency, case-conflict. Keep the
  tree ruff-clean and formatted; do not hand-format around the formatter.
- The shellcheck and hadolint hooks need Docker. `shellcheck-py` is intentionally
  avoided because it requires a Python built with `lzma`.

## Verifying changes

```bash
export PYTHONPATH=src
python -m waw_calendars.fetch_all --out events --source <id> -v
python -m waw_calendars.generate_ics --in events --out calendars --days 14
python -c "import glob,icalendar; [icalendar.Calendar.from_ical(open(f,'rb').read()) for f in glob.glob('calendars/*.ics')]"
```

## Changelog

For every meaningful change, add a dated note under `changelog/` (see
`changelog/README.md`) describing **what** changed and **why**, so future
sessions have context.
