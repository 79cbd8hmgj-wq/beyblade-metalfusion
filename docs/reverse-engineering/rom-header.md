# ROM identity and GBA-header validation

**Confirmed direct binary evidence:** `Beyblade G-Revolution (USA).gba` is exactly 4,194,304 bytes. SHA-256 is `c4a568adc896bace0e25dbff4aa0c1802933c88e3f4a4e825075116c8c4173e5`, SHA-1 is `a89f7b4eb77dc986022201db51a676451ba7c5e4`, and CRC32 is `33afdbe8`.

The internal title is `BEYBLADEGREV`, game code `BB2E`, maker code `70`, version `0`, and fixed byte `0x96`. The stored and calculated complement checksums are both `0x83`; the Nintendo logo matches the official fixed sequence. The entry word is ARM branch `0xEA00002E`, decoded from ROM offset `0x00000000` to `0x000000C0` / runtime `0x080000C0`.

**Strongly supported assessment:** the image is a valid, exact 4 MiB capacity image rather than malformed, trimmed, or overdumped. It has no terminal `0xFF` run, but does have terminal zero fill considered separately in the free-space report. Static analysis cannot independently establish whether an unknown historical patch was applied, so “unmodified retail dump” remains unknown despite the supported hash check.

An null-terminated `EEPROM_V124` signature begins at offset `0x003A93BC` / runtime `0x083A93BC` (**confirmed direct binary evidence**). The older `0x003A937C` value points into preceding text and is rejected. Full machine-readable fields are in `analysis/rom-map/rom-identity.json`.
