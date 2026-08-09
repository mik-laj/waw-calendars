#!/usr/bin/env bash
# Fetch stage: pull events from sources into the YAML store on the data branch.
#
# Usage: scripts/fetch.sh [--source expoxxi] [--throttle 0.5]
# Runs the Python fetcher writing to <worktree>/events, then commits the YAML.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/lib.sh
source "${SCRIPT_DIR}/lib.sh"

PYTHON="${PYTHON:-python}"
export PYTHONPATH="${REPO_ROOT}/src${PYTHONPATH:+:$PYTHONPATH}"

setup_data_worktree

"$PYTHON" -m waw_calendars.fetch_all --out "${REPO_ROOT}/${WORKTREE}/events" "$@"

commit_and_push "fetch: refresh event YAML store ($(date -u +%Y-%m-%dT%H:%MZ))"
