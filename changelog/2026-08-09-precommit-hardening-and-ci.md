# 2026-08-09 — More pre-commit rules + pre-commit CI

## What

- Added pre-commit hooks: `detect-private-key`, `check-executables-have-shebangs`,
  `check-shebang-scripts-are-executable`, `check-case-conflict`, and `hadolint`
  (Docker) for the add-on Dockerfile (with `DL3008` ignored).
- Added `.github/workflows/pre-commit.yml` running all hooks on push/PR to
  `main` (the `data` artifact branch is excluded).

## Why

- Reviewed the file inventory: Python, Bash, YAML/TOML and workflows were
  already covered; the Dockerfile and secret-handling were not. Since the
  project deals with an SSH deploy key, guarding against committing a private
  key is especially worthwhile.
- A CI lint gate enforces the same checks even if a local hook is bypassed.

## Notes

- Markdownlint/codespell were deliberately skipped: the repo is bilingual
  (Polish names/comments), so those tools would mostly produce false positives.
- Docker-based hooks (shellcheck, hadolint) run on ubuntu runners without extra
  setup. Hook envs are cached via `~/.cache/pre-commit`.
- `pre-commit run --all-files` is green with the new rules.
