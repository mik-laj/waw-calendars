#!/usr/bin/env bash
# Add-on entrypoint: set up SSH from the deploy key, refresh the repo checkout,
# then run the fetch + generate stages (which commit/push to the data branch).
# One-shot: runs once and exits (started on a schedule by a HA automation).
set -euo pipefail

OPTIONS=/data/options.json
opt() { python3 -c "import json;print(json.load(open('${OPTIONS}')).get('$1',''))"; }

REPO_URL="$(opt repo_url)"
DATA_BRANCH="$(opt data_branch)"
DEPLOY_KEY_PATH="$(opt deploy_key_path)"
DAYS="$(opt days)"
THROTTLE="$(opt throttle)"
GIT_USER_NAME="$(opt git_user_name)"
GIT_USER_EMAIL="$(opt git_user_email)"

export DATA_BRANCH GIT_USER_NAME GIT_USER_EMAIL
export PYTHON=python3

echo "[waw-calendars] starting run (branch=${DATA_BRANCH}, days=${DAYS})"

# --- SSH setup from the deploy key -----------------------------------------
if [ ! -f "${DEPLOY_KEY_PATH}" ]; then
  echo "[waw-calendars] ERROR: deploy key not found at ${DEPLOY_KEY_PATH}" >&2
  echo "  Place the private key there (see the add-on README) and retry." >&2
  exit 1
fi
mkdir -p /root/.ssh
chmod 700 /root/.ssh
cp "${DEPLOY_KEY_PATH}" /root/.ssh/id_ed25519
chmod 600 /root/.ssh/id_ed25519
ssh-keyscan -t rsa,ed25519 github.com >>/root/.ssh/known_hosts 2>/dev/null
git config --global user.name "${GIT_USER_NAME}"
git config --global user.email "${GIT_USER_EMAIL}"

# --- Refresh code checkout (persistent across runs in /data) ----------------
REPO=/data/repo
if [ ! -d "${REPO}/.git" ]; then
  echo "[waw-calendars] cloning ${REPO_URL}"
  git clone "${REPO_URL}" "${REPO}"
fi
cd "${REPO}"
git remote set-url origin "${REPO_URL}"
git fetch --prune origin
git reset --hard origin/main
# Keep deps in sync with the freshly pulled code.
pip install -q -r requirements.txt

# --- Run the pipeline (each stage commits/pushes to the data branch) --------
scripts/fetch.sh --throttle "${THROTTLE}"
scripts/generate.sh --days "${DAYS}"

echo "[waw-calendars] run complete"
