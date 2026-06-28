#!/usr/bin/env bash
# Build an Ebitengine WebAssembly bundle with a Go-version-aware wasm_exec.js copy.
set -euo pipefail

PROJECT_DIR="${1:-.}"
DIST_DIR="${2:-dist}"
PACKAGE="${PACKAGE:-./cmd/game}"
OUTPUT_NAME="${OUTPUT_NAME:-game.wasm}"

cd "$PROJECT_DIR"
mkdir -p "$DIST_DIR"

GOOS=js GOARCH=wasm go build -trimpath -ldflags="-s -w" -o "$DIST_DIR/$OUTPUT_NAME" "$PACKAGE"

GOROOT="$(go env GOROOT)"
GOVERSION="$(go env GOVERSION | sed 's/go//')"
MAJOR="${GOVERSION%%.*}"
MINOR="${GOVERSION#*.}"
MINOR="${MINOR%%.*}"

if [ "$MAJOR" -gt 1 ] || { [ "$MAJOR" -eq 1 ] && [ "$MINOR" -ge 24 ]; }; then
  WASM_DIR="$GOROOT/lib/wasm"
else
  WASM_DIR="$GOROOT/misc/wasm"
fi

cp "$WASM_DIR/wasm_exec.js" "$DIST_DIR/"

if [ -f "templates/web/index.html" ]; then
  cp "templates/web/index.html" "$DIST_DIR/index.html"
elif [ -f "web/index.html" ]; then
  cp "web/index.html" "$DIST_DIR/index.html"
fi

echo "WASM build complete in $DIST_DIR"
echo "  $DIST_DIR/$OUTPUT_NAME"
echo "  $DIST_DIR/wasm_exec.js"
