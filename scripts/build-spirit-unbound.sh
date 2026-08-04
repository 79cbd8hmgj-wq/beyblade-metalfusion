#!/bin/sh
set -eu
[ "$#" -eq 2 ] || { echo "usage: $0 SOURCE_ROM PROFILE_ID" >&2; exit 2; }
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
exec python3 -m tools.build.build_rom --rom "$1" --profile "$ROOT/data/build/profiles/$2.json" --output-dir "$ROOT/build/generated/$2" --clean
