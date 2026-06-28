#!/usr/bin/env bash
# Build a raylib desktop project with CMake.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${1:-.}"
BUILD_DIR="${2:-build}"
BUILD_TYPE="${BUILD_TYPE:-Release}"

cd "$PROJECT_DIR"

cmake -S . -B "$BUILD_DIR" -DCMAKE_BUILD_TYPE="$BUILD_TYPE"
cmake --build "$BUILD_DIR"

EXE="$(find "$BUILD_DIR" -maxdepth 2 -type f -perm -111 2>/dev/null | head -n 1 || true)"
if [ -n "$EXE" ]; then
  echo "Build complete: $EXE"
  echo "Run from the directory that contains resources/ if your game loads relative assets."
else
  echo "Build complete in $BUILD_DIR"
fi
