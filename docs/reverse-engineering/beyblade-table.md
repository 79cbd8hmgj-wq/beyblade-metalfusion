# Complete Beyblade master table (Task 2)

## Result

The supported US ROM contains **83** code-indexed complete-Beyblade templates at ROM `0x0007A1F4` through `0x0007AEE3` (end-exclusive `0x0007AEE4`; runtime base `0x0807A1F4`). Records are fixed-width **40 bytes**. This is **confirmed** by `getBeyBladeWithIndex` at Thumb address `0x0803DCFC`: it bounds the ID to `0..82`, multiplies it by 40, and adds the table base.

The first/last canonical entries are index 0 **Dragoon S** and index 82 **Rushing Boar**. All 83 records have a display name; no sentinel/blank record occurs. Display-name spelling duplicates can exist across the game, but each canonical row remains distinct. String storage order is reverse of canonical record order and is not used to infer IDs.

## Field map

| Offset | Size | Interpretation | Confidence |
|---:|---:|---|---|
| `0x00` | 20 | five ROM pointers: English, French, German, Italian, Spanish display name | confirmed structure; language labels strongly supported |
| `0x14` | 4 | ROM pointer `field_14_ptr` | confirmed pointer, unknown meaning |
| `0x18` | 4 | ROM pointer `field_18_ptr` | confirmed pointer, unknown meaning |
| `0x1C` | 4 | `field_1c_bytes` packed configuration | unknown semantics |
| `0x20` | 4 | `field_20_bytes` packed configuration | unknown semantics |
| `0x24` | 1 | `field_24_u8`, always zero in all 83 records | unknown/reserved candidate |
| `0x25` | 1 | season/generation selector, range 0–3 | strongly supported by direct season-accessor comparison |
| `0x26` | 2 | `field_26_u16`, always zero in this table | unknown/reserved candidate |

Unknown packed bytes are intentionally not assigned component/stat names. `field-statistics.json` records distributions. Task 3 should begin by following `field_14_ptr`, `field_18_ptr`, and setup code reading offsets `0x1C`–`0x23`, without reconstructing components here.

## Localization is not the master table

`0x000796DC` begins mixed lookup data. Its opening ten slots encode two sequences of localized `None` (`None`, `None`, `Ninguno`, `Nessuno`, `Kein`); subsequent runs contain 10 repeated pointers for 38 earlier complete names and then 5-pointer alternating Bit Beast/Special Move names. At `0x0007A1F4`, the representation changes to 40-byte templates. Thus the pointer-rich precursor is concatenated presentation/localization data, not the complete master.

## Executable and collection relationship

`getRandomBeyBladeFromSeason` at `0x0803DC70` scans IDs 0–82, compares signed byte `record+0x25`, holds at most 32 IDs, selects one through the RNG helper, and returns `base + ID*40`. `getBeyBladeWithIndex` is described above. The string reference for `removeBladeFromTysonsCollection` is a literal-pool anchor near code that scans 83 RAM-related entries, but an actual breakpoint is still needed to separate its caller and callee confidently. A direct pointer to `initBeybladeMenu` occurs at ROM `0x000566AC` in the literal pool following code ending near `0x0005668C`. The reference confirms use, but the behavior and exact enclosing start remain unknown, so no function is named solely from the diagnostic string.

## Runtime status and exact experiment

The supplied debugger bundle was located, but no automated save/gameplay state exists to open the Beyblade menu. Static evidence resolves base/count/stride without a runtime claim. To verify expansion: launch `debugger-bundle/run-mgba-gdb-headless.sh`, break at `*0x0803dcfc`, reach the selection menu, record `r0`, finish the function, and compare `r0` with `0x0807A1F4 + 40*ID`. Break at `*0x0803dc70` during a season reward and record its season argument and returned row. Store transcripts under ignored `analysis/runtime/`.

## Regeneration

```bash
rm -rf analysis/generated/tables/beyblades
python3 -m tools.gba.table_extract --rom "Beyblade G-Revolution (USA).gba" --table beyblades --output analysis/generated/tables/beyblades
```

The extractor validates the supported SHA-256, bounds, emits deterministic JSON/CSV/summary files, and checks byte-perfect parse/serialize round trips. It never writes a ROM.
