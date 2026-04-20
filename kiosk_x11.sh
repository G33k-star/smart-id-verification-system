#!/bin/sh
set -eu

STATE_DIR="${XDG_CACHE_HOME:-$HOME/.cache}/smart-id-verification-system"
KEYMAP_BACKUP="$STATE_DIR/xmodmap.pre-kiosk"

log() {
    echo "[kiosk] $*" >&2
}

require_display() {
    if [ -z "${DISPLAY:-}" ]; then
        log "DISPLAY is not set."
        exit 1
    fi
}

require_xmodmap() {
    if ! command -v xmodmap >/dev/null 2>&1; then
        log "xmodmap is not installed."
        exit 1
    fi
}

save_keymap_backup() {
    mkdir -p "$STATE_DIR"

    if [ ! -f "$KEYMAP_BACKUP" ]; then
        xmodmap -pke > "$KEYMAP_BACKUP"
    fi
}

cleanup_file() {
    file_path=$1

    if [ -n "$file_path" ] && [ -f "$file_path" ]; then
        rm -f "$file_path"
    fi
}

keycodes_for_keysym() {
    map_file=$1
    keysym_name=$2

    awk -v target="$keysym_name" '
        $1 == "keycode" && $2 ~ /^[0-9]+$/ {
            keycode = $2
            for (i = 4; i <= NF; i += 1) {
                if ($i == target && !seen[keycode]++) {
                    print keycode
                }
            }
        }
    ' "$map_file"
}

remember_keycode() {
    seen_file=$1
    keycode=$2

    if grep -qx "$keycode" "$seen_file" 2>/dev/null; then
        return 1
    fi

    printf '%s\n' "$keycode" >> "$seen_file"
    return 0
}

apply_xmodmap_command() {
    command_text=$1

    if ! xmodmap -e "$command_text" >/dev/null 2>&1; then
        log "failed: $command_text"
        return 1
    fi

    return 0
}

clear_modifier_if_present() {
    modifier_name=$1
    map_file=$2
    shift 2

    for keysym_name in "$@"; do
        if [ -n "$(keycodes_for_keysym "$map_file" "$keysym_name")" ]; then
            apply_xmodmap_command "clear ${modifier_name}" || true
            return 0
        fi
    done

    return 0
}

disable_keysym_if_present() {
    keysym_name=$1
    map_file=$2
    disabled_keycodes_file=$3

    keycodes=$(keycodes_for_keysym "$map_file" "$keysym_name")
    if [ -z "$keycodes" ]; then
        log "skip missing keysym ${keysym_name}"
        return 0
    fi

    for keycode in $keycodes; do
        if remember_keycode "$disabled_keycodes_file" "$keycode"; then
            apply_xmodmap_command \
                "keycode ${keycode} = NoSymbol NoSymbol NoSymbol NoSymbol NoSymbol NoSymbol NoSymbol NoSymbol" || true
        fi
    done
}

lock_keys() {
    require_display
    require_xmodmap

    save_keymap_backup

    current_keymap=$(mktemp)
    disabled_keycodes=$(mktemp)
    trap 'cleanup_file "$current_keymap"; cleanup_file "$disabled_keycodes"' EXIT HUP INT TERM

    xmodmap -pke > "$current_keymap"

    clear_modifier_if_present control "$current_keymap" Control_L Control_R
    clear_modifier_if_present mod1 "$current_keymap" Alt_L Alt_R Meta_L Meta_R
    clear_modifier_if_present mod4 "$current_keymap" Super_L Super_R

    for keysym_name in Escape Control_L Control_R Alt_L Alt_R Super_L Super_R Meta_L Meta_R; do
        disable_keysym_if_present "$keysym_name" "$current_keymap" "$disabled_keycodes"
    done

    cleanup_file "$current_keymap"
    cleanup_file "$disabled_keycodes"
    trap - EXIT HUP INT TERM
}

restore_keys() {
    require_display
    require_xmodmap

    if [ ! -f "$KEYMAP_BACKUP" ]; then
        log "No saved keyboard map was found at $KEYMAP_BACKUP."
        exit 1
    fi

    xmodmap "$KEYMAP_BACKUP"
    rm -f "$KEYMAP_BACKUP"
}

enable_numlock() {
    require_display

    if ! command -v numlockx >/dev/null 2>&1; then
        log "numlockx is not installed."
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
