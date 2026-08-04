#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
GDB_BIN="${GDB:-gdb-multiarch}"

if ! command -v "${GDB_BIN}" >/dev/null 2>&1; then
  echo "Required debugger not found: ${GDB_BIN}" >&2
  echo "Install gdb-multiarch or set GDB=/path/to/your/gdb." >&2
  exit 69
fi

exec "${GDB_BIN}" -q -x "${ROOT_DIR}/gdb/gba.gdbinit" "$@"
