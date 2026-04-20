#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
KEYS_LOCKED=0

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

restore_keyboard() {
    if [ "$KEYS_LOCKED" -eq 1 ]; then
        "$SCRIPT_DIR/restore_kiosk_x11.sh" >/dev/null 2>&1 || true
    fi
}

trap restore_keyboard EXIT HUP INT TERM

cd "$SCRIPT_DIR" || exit 1

if [ -n "${DISPLAY:-}" ]; then
    if [ "$(config_flag KIOSK_FORCE_NUMLOCK)" = "1" ]; then
        "$SCRIPT_DIR/kiosk_x11.sh" enable-numlock || true
    fi

    if [ "$(config_flag KIOSK_LOCK_KEYS)" = "1" ]; then
        if "$SCRIPT_DIR/kiosk_x11.sh" lock-keys; then
            KEYS_LOCKED=1
        fi
    fi
fi

python3 "$SCRIPT_DIR/main.py"
