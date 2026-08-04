#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "Usage: $0 /path/to/executable /path/to/output-lib-dir" >&2
  exit 64
fi

BINARY="$(realpath "$1")"
DEST_DIR="$2"

if [[ ! -x "${BINARY}" ]]; then
  echo "Executable not found: ${BINARY}" >&2
  exit 66
fi

mkdir -p "${DEST_DIR}"
declare -A SEEN=()
QUEUE=("${BINARY}")

while [[ ${#QUEUE[@]} -gt 0 ]]; do
  CURRENT="${QUEUE[0]}"
  QUEUE=("${QUEUE[@]:1}")

  if ldd "${CURRENT}" 2>&1 | grep -q 'not found'; then
    echo "Unresolved runtime dependency while inspecting ${CURRENT}:" >&2
    ldd "${CURRENT}" >&2 || true
    exit 1
  fi

  while IFS= read -r LIB_PATH; do
    [[ -n "${LIB_PATH}" && -f "${LIB_PATH}" ]] || continue
    LIB_NAME="$(basename "${LIB_PATH}")"

    case "${LIB_NAME}" in
      linux-vdso.so.*|ld-linux*.so.*|libc.so.*|libm.so.*|libpthread.so.*|libdl.so.*|librt.so.*)
        continue
        ;;
    esac

    if [[ -n "${SEEN[${LIB_PATH}]:-}" ]]; then
      continue
    fi

    SEEN["${LIB_PATH}"]=1
    cp -L "${LIB_PATH}" "${DEST_DIR}/${LIB_NAME}"
    QUEUE+=("${LIB_PATH}")
  done < <(
    ldd "${CURRENT}" \
      | awk '/=> \/.*\(/ { print $3 } /^\// { print $1 }' \
      | sort -u
  )
done

find "${DEST_DIR}" -maxdepth 1 -type f -printf '%f\n' | sort
