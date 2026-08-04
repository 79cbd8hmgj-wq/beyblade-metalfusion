#!/bin/sh
set -eu
[ "$#" -eq 1 ] || { echo "usage: $0 SOURCE_ROM" >&2; exit 2; }
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
SOURCE=$1
EXPECTED=c4a568adc896bace0e25dbff4aa0c1802933c88e3f4a4e825075116c8c4173e5
hash() { sha256sum "$1" | awk '{print $1}'; }
BEFORE=$(hash "$SOURCE")
[ "$BEFORE" = "$EXPECTED" ] || { echo "unsupported source SHA-256: $BEFORE" >&2; exit 1; }
rm -rf "$ROOT/build/temp/build-a" "$ROOT/build/temp/build-b"
mkdir -p "$ROOT/build/temp"
"$ROOT/scripts/build-spirit-unbound.sh" "$SOURCE" infrastructure-smoke
cp -R "$ROOT/build/generated/infrastructure-smoke" "$ROOT/build/temp/build-a"
"$ROOT/scripts/build-spirit-unbound.sh" "$SOURCE" infrastructure-smoke
cp -R "$ROOT/build/generated/infrastructure-smoke" "$ROOT/build/temp/build-b"
diff -qr "$ROOT/build/temp/build-a" "$ROOT/build/temp/build-b"
AFTER=$(hash "$SOURCE")
[ "$AFTER" = "$BEFORE" ] || { echo "source ROM changed" >&2; exit 1; }
