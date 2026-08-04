# Concrete unresolved questions

* Which code references or emits the identifier pools at `0x0033BE50`–`0x0033D358`, and are these debug symbols, script command names, or registration records?
* What are the entry count and field meanings of the candidate pointer run at `0x00000AA0` and higher-ranked runs in `analysis/pointers/table-candidates.json`?
* Which of the 226 structurally valid LZ77 streams are graphics, maps, audio, or general data? Runtime decompression destinations are required; plausible Huffman/RLE/differential headers also need format-specific validation.
* Where exactly do ARM bootstrap code, Thumb game code, literal pools, and non-code data transition? Static density is insufficient for instruction-accurate boundaries.
* **confirmed:** `EEPROM_V124` is at ROM `0x003A93BC` (runtime `0x083A93BC`); its library boundary is documented by the save reconstruction.
* Do any unaligned, computed, or encoded pointers enter the terminal fill at `0x003D52C0`? Twenty-three aligned pointer-like words already target it.
* Which code constructs battle-effective statistics from the Task 3 category-local component IDs, and is menu aggregation identical?

## Task 2 bounded unknowns

Task 3 identifies `+0x1D`, `+0x1E`, and `+0x20` as strongly supported
Attack Ring, Weight Disk, and Blade Base IDs; `+0x1F` remains a packed Spin
Gear/core candidate and `+0x21` a strongly supported Bit Chip ID. The exact
meaning of `+0x1C`, the high Spin Gear bits, and constants at `+0x22/+0x23`
remains unresolved. `field_14_ptr` and `field_18_ptr` are bounded presentation
resource families. Prices, unlock conditions, and the aggregation function
require the exact runtime experiments in the Task 3 reports.

## Task 5 persistence unknowns

* **Unknown:** semantic offsets within payload `0x0004–0x1F5F` (player/settings/time, inventory/loadout, economy, story/tournament and character progression) await controlled copied-save diffs and serializer watchpoints.
* **Unknown:** header words `+0x08` and `+0x0C`; do not call either a version, timestamp, or sequence.
* **Candidate:** timer/DMA/interrupt helper identities and retail visibility of diagnostic output.
* **Strongly supported but not proven free:** EEPROM tail blocks `0x3EF–0x3FF`; indirect access/runtime scan remains required.

## Task 6 exact runtime work

All items are **unknown** pending a live mGBA session: break on the binding
consumer after reads of `0x08094F00`; watch `0x0809B350` during a normal and a
tournament battle; watch runtime base `*[0x03000198] + 0x15C8..0x15D3` across
init/award/reset; break `0x08042F08` and record r0-r3 plus the 55×0x30 record
region; and break serializer `0x08045198` while those watched bytes change.
Use only copied saves and the commands in `debugger-bundle/task6-events.gdb`.

## Task 8 unresolved runtime hooks

* **unknown:** exact New Game hook for the creator state machine.
* **unknown:** text renderer substitution hook for player-facing Tyson/Takao paths.
* **unknown:** player sprite and portrait loader hooks.
* **unknown:** dynamic proof that EEPROM tail blocks `0x3EF-0x3FF` survive every original subsystem.
