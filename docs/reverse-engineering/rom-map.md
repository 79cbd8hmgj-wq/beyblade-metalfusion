# First-pass ROM map

## Identity

The supported US ROM is 4 MiB, SHA-256 `c4a568adc896bace0e25dbff4aa0c1802933c88e3f4a4e825075116c8c4173e5`, with a valid logo/checksum and entry at `0x080000C0`. See the header report for all identifiers.

## Top-level ranges

This compact map deliberately coalesces 64 KiB evidence windows. Labels describe the dominant static signal and do not exclude overlap.

| ROM offsets | Runtime addresses | First-pass interpretation | Confidence/evidence |
|---|---|---|---|
| `0x00000000`–`0x000000C0` | `0x08000000`–`0x080000C0` | GBA header | confirmed header validation |
| `0x000000C0`–`0x000800C0` | `0x080000C0`–`0x080800C0` | code/literals with many incidental printable runs | candidate; entry and pointers, no full disassembly |
| `0x000800C0`–`0x000B00C0` | `0x080800C0`–`0x080B00C0` | mixed code/literal pool | candidate pointer density |
| `0x000B00C0`–`0x000E00C0` | `0x080B00C0`–`0x080E00C0` | compressed-data-rich | strongly supported validated streams |
| `0x000E00C0`–`0x002000C0` | `0x080E00C0`–`0x082000C0` | heterogeneous structured/string/data | candidate printable and pointer density |
| `0x002000C0`–`0x003300C0` | `0x082000C0`–`0x083300C0` | mixed compressed/structured data | candidate/strongly supported per window |
| `0x003300C0`–`0x003B00C0` | `0x083300C0`–`0x083B00C0` | identifier/string-rich data and library signature | strongly supported strings; code boundaries unknown |
| `0x003B00C0`–`0x003D00C0` | `0x083B00C0`–`0x083D00C0` | unknown heterogeneous data | unknown |
| `0x003D00C0`–`0x00400000` | `0x083D00C0`–`0x08400000` | fill-dominated tail | strongly supported fill; safety questionable |

The machine map provides every window’s entropy, dominant-byte fraction, string count, pointer count, and validated-stream count. “String pool” in that coarse file means printable-run density, not proven UI text.

## Important evidence

All 13 requested anchors were located. Tournament names occupy `0x0033BE50`–`0x0033BF70`, battle names `0x0033C274`–`0x0033C77C`, and collection names `0x0033D1C4`–`0x0033D358`; `initBeybladeMenu` is at `0x003A8990`. The aligned pointer scan found 48,159 candidates and 1,341 runs. A ten-entry ROM-target run begins at `0x00000AA0`, but table purpose remains a candidate.

There are 226 structurally validated bounded LZ77 streams. The first credible one starts at `0x000BB8CC`, consumes 353 bytes, and claims 732 output bytes. Category assignment remains unknown because no decompression destination or consumer was observed. The sole tracked save signature is `EEPROM_V124` at `0x003A93BC` / `0x083A93BC` (**confirmed**). No audio engine is named from ambiguous static patterns.

## Boundaries and regeneration

Instruction-accurate code/data boundaries, asset meanings, format-specific validation of scanned Huffman/RLE/differential headers, computed references, and safe free space remain unresolved. Regenerate both compact and ignored full evidence with:

```bash
python3 -m tools.gba.rom_map --rom "Beyblade G-Revolution (USA).gba" --tracked-output analysis --generated-output analysis/generated --clean-generated
```
