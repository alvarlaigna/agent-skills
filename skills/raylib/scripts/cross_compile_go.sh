#!/usr/bin/env bash
# Cross-compile a raylib-go desktop binary.
set -euo pipefail

TARGET="${1:-windows}"
OUTPUT="${2:-dist/game}"
MAIN="${MAIN:-.}"

case "$TARGET" in
  windows)
    CGO_ENABLED=1 CC=x86_64-w64-mingw32-gcc GOOS=windows GOARCH=amd64 \
      go build -ldflags "-s -w -H=windowsgui" -o "${OUTPUT}.exe" "$MAIN"
    ;;
  darwin)
    CGO_ENABLED=1 CC=x86_64-apple-darwin21.1-clang GOOS=darwin GOARCH=amd64 \
      go build -ldflags "-linkmode external -s -w '-extldflags=-mmacosx-version-min=10.15'" \
      -o "$OUTPUT" "$MAIN"
    ;;
  linux)
    CGO_ENABLED=1 GOOS=linux GOARCH=amd64 \
      go build -ldflags "-s -w" -o "$OUTPUT" "$MAIN"
    ;;
  *)
    echo "usage: $0 [windows|darwin|linux] [output-path]" >&2
    exit 1
    ;;
esac

echo "Built $TARGET binary: $OUTPUT"
