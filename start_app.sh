#!/bin/sh

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

cd "$SCRIPT_DIR" || exit 1
exec /usr/bin/env python3 "$SCRIPT_DIR/main.py"
