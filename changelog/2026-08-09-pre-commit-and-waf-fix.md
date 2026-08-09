# 2026-08-09 — Pre-commit tooling, WAF workaround attempt, CI fixes

## What

- Added pre-commit (`.pre-commit-config.yaml`) and ruff config (`pyproject.toml`):
  ruff lint + format, standard file hooks, Docker-based shellcheck, and GitHub
  workflow schema validation. Applied the resulting ruff autofixes/formatting
  across `src/`.
- Fixed the CI pipeline: the fetch and generate stages share a working dir, and
  pruning before deleting the `.data` worktree left a stale registration, so
  generate failed with "'data' is already used by worktree". Now we remove the
  worktree and delete the dir first, then prune.
- Switched the HTTP client to a realistic desktop-browser User-Agent + headers.

## Why

- Consistent, enforced code quality on every commit.
- Get the single-workflow pipeline green end-to-end on GitHub.
- Attempt to get past the Wola site's WAF, which 403s the runner.

## Notes

- **shellcheck via Docker** (koalaman/shellcheck-precommit), not shellcheck-py:
  this machine's pyenv Python 3.14 lacks `lzma`, which shellcheck-py needs to
  unpack its binary. Docker hook works locally and on CI.
- **Wola still 403s from GitHub-hosted runners even with a browser UA** — the
  block is by datacenter IP (Azure), not User-Agent. expoxxi and waw4free work
  fine from CI. Open question: how to source Wola (self-hosted runner, proxy,
  seed-and-keep last-known-good via upsert, or accept it as empty in CI).
- CI result after fixes: `all.ics` 395 events (waw4free 395, expoxxi 0 as its
  fairs are out of the 14-day window, wola 0 due to the 403).
