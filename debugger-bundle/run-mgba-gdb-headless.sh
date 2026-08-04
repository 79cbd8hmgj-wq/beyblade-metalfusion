#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"

if [[ $# -lt 1 ]]; then
  cat >&2 <<'EOF'
Usage: ./run-mgba-gdb-headless.sh [mGBA options] /path/to/game.gba

Starts mGBA without a visible window or audio device and exposes the ARMv4T
GDB server on 127.0.0.1:2345.
EOF
  exit 64
fi

export LD_LIBRARY_PATH="${ROOT_DIR}/lib${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}"
export SDL_VIDEODRIVER="${SDL_VIDEODRIVER:-dummy}"
export SDL_AUDIODRIVER="${SDL_AUDIODRIVER:-dummy}"

exec "${ROOT_DIR}/mgba" -g "$@"
