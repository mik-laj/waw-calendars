#!/usr/bin/env bash
# Generate stage: build .ics calendars from the YAML store on the data branch.
#
# Usage: scripts/generate.sh [--days 14]
# Reads <worktree>/events, writes <worktree>/calendars, then commits the .ics.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/lib.sh
source "${SCRIPT_DIR}/lib.sh"

PYTHON="${PYTHON:-python}"
export PYTHONPATH="${REPO_ROOT}/src${PYTHONPATH:+:$PYTHONPATH}"

setup_data_worktree

"$PYTHON" -m waw_calendars.generate_ics \
  --in "${REPO_ROOT}/${WORKTREE}/events" \
  --out "${REPO_ROOT}/${WORKTREE}/calendars" "$@"

commit_and_push "generate: rebuild .ics calendars ($(date -u +%Y-%m-%dT%H:%MZ))"
