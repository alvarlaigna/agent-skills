#!/usr/bin/env bash
# Build desktop release binaries for common targets.
set -euo pipefail

PROJECT_DIR="${1:-.}"
DIST_DIR="${2:-dist}"
PACKAGE="${PACKAGE:-./cmd/game}"
NAME="${NAME:-game}"

cd "$PROJECT_DIR"
mkdir -p "$DIST_DIR"

LDFLAGS='-s -w'
COMMON=(go build -trimpath -ldflags="$LDFLAGS")

GOOS=windows GOARCH=amd64 "${COMMON[@]}" -ldflags="$LDFLAGS -H=windowsgui" -o "$DIST_DIR/${NAME}.exe" "$PACKAGE"
GOOS=linux GOARCH=amd64 "${COMMON[@]}" -o "$DIST_DIR/${NAME}" "$PACKAGE"
GOOS=darwin GOARCH=arm64 "${COMMON[@]}" -o "$DIST_DIR/${NAME}_darwin_arm64" "$PACKAGE"

echo "Release builds written to $DIST_DIR"
