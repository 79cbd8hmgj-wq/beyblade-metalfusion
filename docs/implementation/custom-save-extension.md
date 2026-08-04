# Custom save extension

## Implemented

The Python/tooling model uses two 64-byte transaction slots in the EEPROM tail: slot A blocks `0x3EF-0x3F6`, slot B blocks `0x3F7-0x3FE`, with block `0x3FF` reserved. Slot parsing uses explicit persisted-field names, CRC32, schema checking, commit magic, and wraparound-aware sequence selection.

## Correctness boundaries

The save editor is explicitly experimental because dynamic tail safety is not confirmed. Editing requires `--allow-unverified-tail-extension`, refuses in-place writes, warns on stderr, preserves every byte before `0x1F78`, and preserves wrapper/padding bytes after `0x2000`.

## Unknown / unexecuted

Native EEPROM writes are disabled until mGBA/GDB evidence proves no original subsystem reads or writes blocks `0x3EF-0x3FF`.
