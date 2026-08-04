#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "${TMP_DIR}"' EXIT

BUNDLE="${TMP_DIR}/bundle"
BIN_DIR="${TMP_DIR}/bin"
mkdir -p "${BUNDLE}" "${BIN_DIR}"

cat > "${BUNDLE}/mgba" <<'MGBA'
#!/usr/bin/env bash
exit 0
MGBA
chmod +x "${BUNDLE}/mgba"

# Deliberately omit '-g' from help text. A working end-to-end GDB connection,
# not formatting of help output, must determine whether the bundle passes.
printf 'mGBA test frontend\n' > "${BUNDLE}/mgba-help.txt"

cat > "${BUNDLE}/run-mgba-gdb-headless.sh" <<'LAUNCHER'
#!/usr/bin/env bash
exec python3 - <<'PY'
import socket
import time

listener = socket.socket()
listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
listener.bind(("127.0.0.1", 2345))
listener.listen(1)
time.sleep(30)
PY
LAUNCHER
chmod +x "${BUNDLE}/run-mgba-gdb-headless.sh"

cat > "${BIN_DIR}/gdb-multiarch" <<'GDB'
#!/usr/bin/env bash
printf 'r0             0x00000000\npc             0x080000c0\n'
GDB
chmod +x "${BIN_DIR}/gdb-multiarch"

printf '\0' > "${TMP_DIR}/test.gba"

PATH="${BIN_DIR}:${PATH}" \
  bash "${ROOT_DIR}/scripts/verify-gdb-bundle.sh" \
  "${BUNDLE}" "${TMP_DIR}/test.gba"

grep -q 'mGBA ARM GDB smoke test: PASS' "${BUNDLE}/GDB_SMOKE_TEST.txt"

# The verifier must terminate its launched server. Leaving this port occupied
# would cause the following real mGBA test to connect to the fake listener.
for _ in $(seq 1 20); do
  if ! awk '$2 ~ /:0929$/ && $4 == "0A" { found=1 } END { exit !found }' /proc/net/tcp; then
    exit 0
  fi
  sleep 0.05
done

echo "Regression test leaked a listener on 127.0.0.1:2345" >&2
exit 1
