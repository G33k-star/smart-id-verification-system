#!/usr/bin/env bash
set -euo pipefail

echo "[backup] Starting data backup..."

repo_root="$(git rev-parse --show-toplevel)"
cd "$repo_root"

if [[ "$(git rev-parse --abbrev-ref HEAD)" != "main" ]]; then
  echo "[backup] Refusing to run: current branch is not main." >&2
  exit 1
fi

if git diff --cached --name-only | grep -qv '^data/'; then
  echo "[backup] Refusing to run: staged changes exist outside data/." >&2
  exit 1
fi

git add -f -A -- data/

if git diff --cached --quiet -- data/; then
  echo "[backup] No data changes to back up."
  exit 0
fi

timestamp="$(date -u '+%Y-%m-%d %H:%M:%S UTC')"
git commit -m "Backup data ${timestamp}"
git push origin main

echo "[backup] Data backup complete."
