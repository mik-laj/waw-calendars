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
- **Wola 403 confirmed as an IP block, not a header issue.** A temporary
  `wola-probe` workflow tested the runner (Azure IP 172.183.132.66) against the
  feed, root page and an event subpage with default UA, browser UA, extra
  headers and HTTP/1.1 — all 403; expoxxi/waw4free were 200. The 403 body is the
  city portal's own "Strona nie może zostać wyświetlona – PIUW" page. So no
  header/UA tweak helps; Wola needs a Polish/residential egress (self-hosted
  runner or proxy). The browser-UA change was kept (harmless, good default) but
  it does not unblock Wola. Probe workflow removed after diagnosis.
- CI result after fixes: `all.ics` 395 events (waw4free 395, expoxxi 0 as its
  fairs are out of the 14-day window, wola 0 due to the 403).
