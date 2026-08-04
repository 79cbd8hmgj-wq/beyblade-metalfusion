#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "Usage: $0 /path/to/bundle /path/to/test.gba" >&2
  exit 64
fi

BUNDLE="$(realpath "$1")"
ROM="$(realpath "$2")"
LOG="${BUNDLE}/GDB_SMOKE_TEST.txt"
EMU_LOG="$(mktemp)"
GDB_LOG="$(mktemp)"
PID=""

cleanup() {
  if [[ -n "${PID}" ]] && kill -0 "${PID}" 2>/dev/null; then
    kill "${PID}" 2>/dev/null || true
    wait "${PID}" 2>/dev/null || true
  fi
  rm -f "${EMU_LOG}" "${GDB_LOG}"
}
trap cleanup EXIT

[[ -x "${BUNDLE}/mgba" ]]
[[ -x "${BUNDLE}/run-mgba-gdb-headless.sh" ]]
[[ -f "${ROM}" ]]

printf 'Starting mGBA ARM GDB smoke test...\n'
"${BUNDLE}/run-mgba-gdb-headless.sh" "${ROM}" >"${EMU_LOG}" 2>&1 &
PID=$!

LISTENING=0
for _ in $(seq 1 40); do
  if awk '$2 ~ /:0929$/ && $4 == "0A" { found=1 } END { exit !found }' /proc/net/tcp; then
    LISTENING=1
    break
  fi
  if ! kill -0 "${PID}" 2>/dev/null; then
    echo "mGBA exited before opening its GDB server:" >&2
    cat "${EMU_LOG}" >&2
    exit 1
  fi
  sleep 0.25
done

if [[ ${LISTENING} -ne 1 ]]; then
  echo "mGBA did not listen on 127.0.0.1:2345" >&2
  cat "${EMU_LOG}" >&2
  exit 1
fi

printf 'mGBA is listening on 127.0.0.1:2345; connecting GDB...\n'
if ! gdb-multiarch -q -batch \
  -ex 'set pagination off' \
  -ex 'set confirm off' \
  -ex 'set endian little' \
  -ex 'set architecture armv4t' \
  -ex 'target remote 127.0.0.1:2345' \
  -ex 'info registers' \
  -ex 'x/4i $pc' \
  -ex 'disconnect' >"${GDB_LOG}" 2>&1; then
  echo "gdb-multiarch could not complete the remote debugging session:" >&2
  cat "${GDB_LOG}" >&2
  echo "mGBA transcript:" >&2
  cat "${EMU_LOG}" >&2
  exit 1
fi

if ! grep -Eq '^pc[[:space:]]+0x|^r0[[:space:]]+0x' "${GDB_LOG}"; then
  echo "GDB connected but did not return the expected ARM register output:" >&2
  cat "${GDB_LOG}" >&2
  exit 1
fi

{
  echo "mGBA ARM GDB smoke test: PASS"
  echo "Endpoint: 127.0.0.1:2345"
  echo "Test ROM: generated 512-byte GBA image"
  echo
  echo "GDB transcript:"
  cat "${GDB_LOG}"
  echo
  echo "mGBA transcript:"
  cat "${EMU_LOG}"
} >"${LOG}"

printf 'Verified mGBA ARM GDB server and register access.\n'
