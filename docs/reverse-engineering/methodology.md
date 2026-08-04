# Task 1 methodology

## Evidence model

Every report separates **direct binary evidence** (hashes, header bytes, exact matches, parsed streams), **structural inference** (density and table shapes), **runtime evidence** (none collected in Task 1), and **hypothesis**. Conclusions use `confirmed`, `strongly_supported`, `candidate`, or `unknown`. “Confirmed” validates a measurable property, not the semantic purpose of the containing data.

The driver reads the ROM once, hashes it before analysis, reads and hashes it again afterward, and never opens it for writing. Scans are deterministic. Aligned little-endian pointer candidates are range checked and ROM mirrors normalized. ASCII runs are catalogued with termination, prefix, alignment, duplicates, nearby clusters, and aligned references. LZ77 streams must parse completely within input and an 8 MiB output bound; tiny chance matches are rejected.

## Limitations and rejected interpretations

ASCII and instruction plausibility occur accidentally in graphics/audio. Thus coarse regions are deliberately overlapping hypotheses, not a disassembly. A pointer-like word does not prove a pointer, consecutive pointers do not prove table semantics, uniform fill does not alone prove free space, and a valid compressed stream does not alone identify graphics. The `EEPROM_V` text is direct evidence for a save-library signature, but its precise library version and reachable code extent remain unproven.

## Reproduction

```bash
python3 -m tools.gba.rom_map --rom "Beyblade G-Revolution (USA).gba" --tracked-output analysis --generated-output analysis/generated --clean-generated
```

Delete `analysis/generated/` to demonstrate clean regeneration. Compact JSON/CSV is tracked; full string, pointer, and compression listings remain ignored.
