# 2026-08-09 — Run from home via a Home Assistant add-on

## What

- Added a local Home Assistant add-on in `addons/waw_calendars/` (config.yaml,
  Dockerfile, run.sh, README) that runs the full pipeline from the home network
  and pushes to the `data` branch.
- Added `docs/home-assistant.md` (architecture, deploy-key setup, the scheduling
  automation, verification and troubleshooting).
- Disabled the GitHub Actions `schedule` trigger; the workflow is now a manual
  fallback only. Updated README to say the pipeline runs from home.

## Why

Wola blocks cloud/datacenter IPs (confirmed earlier), so the pipeline must run
from a Polish/residential IP. The user runs Home Assistant (HA OS) on a home
NUC; a local add-on is the cleanest way to run a containerised job there and
reuse the existing scripts unchanged.

## Notes

- **Trigger via `hassio.addon_start`** from a time-pattern automation, not
  `shell_command`: on HA OS the Core container running `shell_command` has no
  Supervisor access nor our code/deps. The add-on holds everything; HA just
  starts it (one-shot: runs once and exits).
- **Auth via SSH deploy key** (write access), read from
  `/config/waw_calendars/deploy_key`. The add-on clones over SSH and pushes to
  `data` with it.
- Image is `python:3.12-slim` (prebuilt lxml wheels). Deps are installed at
  build time and reconciled at runtime after pulling the latest code into a
  persistent `/data/repo` checkout.
- The existing scripts (`scripts/*.sh`) are reused as-is; the add-on only sets
  env (DATA_BRANCH, GIT_USER_*, PYTHON) and SSH before invoking them.
