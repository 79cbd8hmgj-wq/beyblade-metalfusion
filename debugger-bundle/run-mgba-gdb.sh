#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"

if [[ $# -lt 1 ]]; then
  cat >&2 <<'EOF'
Usage: ./run-mgba-gdb.sh [mGBA options] /path/to/game.gba

Starts mGBA with its ARMv4T GDB server listening on 127.0.0.1:2345.
The final argument should be a GBA ROM or ELF file.
EOF
  exit 64
fi

export LD_LIBRARY_PATH="${ROOT_DIR}/lib${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}"

exec "${ROOT_DIR}/mgba" -g "$@"
