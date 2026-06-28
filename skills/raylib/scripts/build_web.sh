#!/usr/bin/env bash
# Build a raylib game for web with emcc and verified linker flags.
set -euo pipefail

PROJECT_DIR="${1:-.}"
OUTPUT="${2:-game.html}"
MAIN="${MAIN:-main.c}"
RAYLIB_PATH="${RAYLIB_PATH:-}"
SHELL_FILE="${SHELL_FILE:-web/minshell.html}"
RESOURCES="${RESOURCES:-resources}"

cd "$PROJECT_DIR"

if [ -z "$RAYLIB_PATH" ]; then
  echo "error: set RAYLIB_PATH to a raylib install with libraylib.web.a" >&2
  exit 1
fi

if [ ! -f "$RAYLIB_PATH/src/libraylib.web.a" ]; then
  echo "error: libraylib.web.a not found under $RAYLIB_PATH/src" >&2
  exit 1
fi

PRELOAD=()
if [ -d "$RESOURCES" ]; then
  PRELOAD=(--preload-file "$RESOURCES")
fi

emcc -o "$OUTPUT" "$MAIN" -Os -Wall \
  "$RAYLIB_PATH/src/libraylib.web.a" \
  -I"$RAYLIB_PATH/src" \
  -sUSE_GLFW=3 \
  -sASYNCIFY \
  -sGL_ENABLE_GET_PROC_ADDRESS=1 \
  -sFORCE_FILESYSTEM=1 \
  -sTOTAL_MEMORY=67108864 \
  --shell-file "$SHELL_FILE" \
  "${PRELOAD[@]}"

echo "Web build complete: $OUTPUT"
