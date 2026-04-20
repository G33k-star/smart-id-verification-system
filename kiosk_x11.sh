#!/bin/sh
set -eu

STATE_DIR="${XDG_CACHE_HOME:-$HOME/.cache}/smart-id-verification-system"
KEYMAP_BACKUP="$STATE_DIR/xmodmap.pre-kiosk"

require_display() {
    if [ -z "${DISPLAY:-}" ]; then
        echo "[kiosk] DISPLAY is not set." >&2
        exit 1
    fi
}

save_keymap_backup() {
    mkdir -p "$STATE_DIR"

    if [ ! -f "$KEYMAP_BACKUP" ]; then
        xmodmap -pke > "$KEYMAP_BACKUP"
    fi
}

lock_keys() {
    require_display

    if ! command -v xmodmap >/dev/null 2>&1; then
        echo "[kiosk] xmodmap is not installed." >&2
        exit 1
    fi

    save_keymap_backup

    xmodmap -e "clear control"
    xmodmap -e "clear mod1"
    xmodmap -e "clear mod4"

    for keysym_name in Escape Control_L Control_R Alt_L Alt_R Super_L Super_R Meta_L Meta_R; do
        xmodmap -e "keysym ${keysym_name} = NoSymbol"
    done
}

restore_keys() {
    require_display

    if ! command -v xmodmap >/dev/null 2>&1; then
        echo "[kiosk] xmodmap is not installed." >&2
        exit 1
    fi

    if [ ! -f "$KEYMAP_BACKUP" ]; then
        echo "[kiosk] No saved keyboard map was found at $KEYMAP_BACKUP." >&2
        exit 1
    fi

    xmodmap "$KEYMAP_BACKUP"
    rm -f "$KEYMAP_BACKUP"
}

enable_numlock() {
    require_display

    if ! command -v numlockx >/dev/null 2>&1; then
        echo "[kiosk] numlockx is not installed." >&2
        exit 1
    fi

    numlockx on
}

case "${1:-}" in
    lock-keys)
        lock_keys
        ;;
    restore-keys)
        restore_keys
        ;;
    enable-numlock)
        enable_numlock
        ;;
    *)
        echo "Usage: $0 {lock-keys|restore-keys|enable-numlock}" >&2
        exit 1
        ;;
esac
