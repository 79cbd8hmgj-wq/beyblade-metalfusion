# EEPROM library (Task 5)

## Findings

**Confirmed:** the sole null-terminated signature is `EEPROM_V124` at ROM `0x003A93BC`, runtime `0x083A93BC`. **Strongly supported:** boot passes `0x40` to Thumb routine `0x080674BC`; its selected parameters and the game loops establish a 64-Kbit EEPROM: `0x2000` bytes, `0x400` eight-byte blocks, 14 serial address bits, maximum block `0x3FF`.

| Runtime | Structural label | Interface/result | Confidence |
|---|---|---|---|
| `0x080674BC` | configure | `r0=0x40` selects large configuration | strongly_supported |
| `0x08067584` | read dword | block index and 8-byte destination | strongly_supported |
| `0x08067634` | program wrapper | forwards to `0x08067648` | strongly_supported |
| `0x08067648` | extended program | emits command/payload and waits | strongly_supported |
| `0x080677A8` | verify | compares four halfwords; mismatch `0x8000` | strongly_supported |
| `0x08067800` | program+verify retry | at most three library attempts | strongly_supported |

DMA/timer/interrupt helper identities are **candidate** pending the supplied debugger experiment; no external SDK name is treated as evidence. Game-level payload/header loops add an eight-attempt policy. Regenerate the compact ROM report with `python3 -m tools.gba.save_format --rom "Beyblade G-Revolution (USA).gba" --output analysis/generated/saves/static-report.json`.
