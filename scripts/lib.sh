#!/usr/bin/env bash
# Shared helpers for the fetch/generate pipelines.
#
# The data branch (default: "data") is an orphan branch that holds only the
# generated artifacts (YAML store + .ics calendars). We check it out into a git
# worktree so the code branch stays clean, write artifacts there, then commit
# and push only when something actually changed.
set -euo pipefail

DATA_BRANCH="${DATA_BRANCH:-data}"
WORKTREE="${WORKTREE:-.data}"
GIT_USER_NAME="${GIT_USER_NAME:-github-actions[bot]}"
GIT_USER_EMAIL="${GIT_USER_EMAIL:-41898282+github-actions[bot]@users.noreply.github.com}"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Prepare $WORKTREE checked out to the data branch (creating it if missing).
setup_data_worktree() {
  cd "$REPO_ROOT"
  git worktree prune >/dev/null 2>&1 || true
  rm -rf "$WORKTREE"
  git fetch origin "$DATA_BRANCH" >/dev/null 2>&1 || true

  if git show-ref --verify --quiet "refs/remotes/origin/${DATA_BRANCH}"; then
    git worktree add -B "$DATA_BRANCH" "$WORKTREE" "origin/${DATA_BRANCH}"
  else
    echo "data branch '${DATA_BRANCH}' not found — creating orphan branch"
    git worktree add --detach "$WORKTREE"
    (
      cd "$WORKTREE"
      git checkout --orphan "$DATA_BRANCH"
      git reset --hard
      git clean -fdx
    )
  fi
  mkdir -p "${WORKTREE}/events" "${WORKTREE}/calendars"
}

# commit_and_push "<commit message>"
commit_and_push() {
  local message="$1"
  cd "${REPO_ROOT}/${WORKTREE}"
  git add -A
  if git diff --cached --quiet; then
    echo "no changes to commit on '${DATA_BRANCH}'"
    return 0
  fi
  git -c "user.name=${GIT_USER_NAME}" -c "user.email=${GIT_USER_EMAIL}" \
    commit -m "$message"
  git push origin "HEAD:${DATA_BRANCH}"
  echo "pushed to '${DATA_BRANCH}'"
}

# Remove the worktree (best effort).
cleanup_worktree() {
  cd "$REPO_ROOT"
  git worktree remove --force "$WORKTREE" >/dev/null 2>&1 || rm -rf "$WORKTREE"
}
