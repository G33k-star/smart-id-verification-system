#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
STATE_DIR="${XDG_CACHE_HOME:-$HOME/.cache}/smart-id-verification-system"
KEYMAP_BACKUP="$STATE_DIR/xmodmap.pre-kiosk"
LOG_FILE="${HOME:-$SCRIPT_DIR}/smart-id-kiosk.log"
KEYS_LOCKED=0
RETRY_PID=""

config_flag() {
    python3 - "$SCRIPT_DIR" "$1" <<'PY'
import importlib.util
import pathlib
import sys

script_dir = pathlib.Path(sys.argv[1])
setting_name = sys.argv[2]

spec = importlib.util.spec_from_file_location("app_config", script_dir / "config.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

print("1" if bool(getattr(module, setting_name, False)) else "0")
PY
}

log_message() {
    timestamp=$(date '+%Y-%m-%d %H:%M:%S' 2>/dev/null || printf 'unknown-time')
    printf '%s [kiosk] %s\n' "$timestamp" "$1" >> "$LOG_FILE"
}

attempt_key_lock() {
    attempt_name=$1

    log_message "key lock attempt: ${attempt_name}"
    if "$SCRIPT_DIR/kiosk_x11.sh" lock-keys >> "$LOG_FILE" 2>&1; then
        KEYS_LOCKED=1
        log_message "key lock success: ${attempt_name}"
        return 0
    fi

    log_message "key lock failed: ${attempt_name}"
    return 1
}

start_key_lock_retries() {
    (
        sleep 2
        attempt_key_lock "retry-2s" || true

        sleep 3
        attempt_key_lock "retry-5s" || true
    ) &
    RETRY_PID=$!
}

stop_key_lock_retries() {
    if [ -n "$RETRY_PID" ]; then
        kill "$RETRY_PID" >/dev/null 2>&1 || true
        wait "$RETRY_PID" >/dev/null 2>&1 || true
        RETRY_PID=""
    fi
}

restore_keyboard() {
    stop_key_lock_retries

    if [ "$KEYS_LOCKED" -eq 1 ] || [ -f "$KEYMAP_BACKUP" ]; then
        log_message "restoring keyboard map"
        "$SCRIPT_DIR/restore_kiosk_x11.sh" >> "$LOG_FILE" 2>&1 || true
    fi
}

trap restore_keyboard EXIT HUP INT TERM

cd "$SCRIPT_DIR" || exit 1

if [ -n "${DISPLAY:-}" ]; then
    if [ "$(config_flag KIOSK_FORCE_NUMLOCK)" = "1" ]; then
        "$SCRIPT_DIR/kiosk_x11.sh" enable-numlock || true
    fi

    if [ "$(config_flag KIOSK_LOCK_KEYS)" = "1" ]; then
        attempt_key_lock "initial" || true
        start_key_lock_retries
    fi
fi

python3 "$SCRIPT_DIR/main.py"
