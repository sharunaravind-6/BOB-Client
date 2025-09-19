#!/usr/bin/env bash
set -euo pipefail

BOT_FILENAME="${1:-}"

if [[ -z "$BOT_FILENAME" ]]; then
  exit 2
fi

if [[ ! -f "$BOT_FILENAME" ]]; then
  exit 3
fi

# Where to put the binary
OUT="./bot"

# Extra compiler flags (warnings, optimization optional)
CXXFLAGS=(-std=c++17 -I/usr/local/include -Wall -Wextra -Wpedantic)

if ! g++ "${CXXFLAGS[@]}" "$BOT_FILENAME" -o "$OUT"; then
  exit 1
fi


# If you want to limit runtime or memory inside container, consider 'timeout' or 'cgroups' (not used here)
# Run the compiled program and capture both stdout and stderr to console
./"$OUT" 2>&1
EXIT_CODE=$?

exit $EXIT_CODE
