#!/usr/bin/env bash
set -euo pipefail

echo "[backup] Starting data backup..."

repo_root="$(git rev-parse --show-toplevel)"
cd "$repo_root"

has_non_data_paths() {
  while IFS= read -r path; do
    [[ -z "$path" ]] && continue
    case "$path" in
      data/*) ;;
      *)
        echo "$path"
        return 0
        ;;
    esac
  done

  return 1
}

if [[ "$(git rev-parse --abbrev-ref HEAD)" != "main" ]]; then
  echo "[backup] Refusing to run: current branch is not main." >&2
  exit 1
fi

if non_data_path="$(has_non_data_paths < <(git diff --name-only))"; then
  echo "[backup] Refusing to run: unstaged changes exist outside data/: ${non_data_path}" >&2
  exit 1
fi

if non_data_path="$(has_non_data_paths < <(git diff --cached --name-only))"; then
  echo "[backup] Refusing to run: staged changes exist outside data/: ${non_data_path}" >&2
  exit 1
fi

if non_data_path="$(has_non_data_paths < <(git ls-files --others --exclude-standard))"; then
  echo "[backup] Refusing to run: untracked files exist outside data/: ${non_data_path}" >&2
  exit 1
fi

if ! git pull --rebase --autostash origin main; then
  echo "[backup] git pull --rebase failed. Resolve the repository state and try again." >&2
  exit 1
fi

git add -f -A -- data/

if git diff --cached --quiet -- data/; then
  echo "[backup] No data changes to back up."
  exit 0
fi

timestamp="$(date -u '+%Y-%m-%d %H:%M:%S UTC')"

if ! git commit -m "Backup data ${timestamp}"; then
  echo "[backup] Commit failed." >&2
  exit 1
fi

if ! git push origin main; then
  echo "[backup] Push failed." >&2
  exit 1
fi

echo "[backup] Data backup complete."
