# Serialized payload

The payload is exactly `0x1F60` bytes. Offset `0x0000` is its stored checksum. Coverage is `0x0004–0x1F5F`, interpreted as 2007 aligned little-endian 32-bit words with wrapping addition. Header `+0x04` duplicates the result; no secondary checksum was found (**strongly_supported**).

The serializer begins at `0x08045198`; the inverse begins at `0x08045590`. Most payload fields remain semantically unresolved, but the copy map is no longer one undifferentiated range.

## Confirmed translated record table

Runtime and instruction evidence identify an 83-record translated table at payload `0x02E8–0x06CB`:

| Property | Value |
|---|---:|
| Records | `83` |
| Payload stride | `0x0C` |
| Runtime stride | `0x28` |
| Serialized bytes per record | `0x0A` |
| Padding per record | `0x02` |
| Serializer loop | `0x08045412–0x080454A0` |
| Deserializer loop | `0x08045844–0x08045954` |

For record `i`, both directions use payload bytes:

```text
0x02E8 + i*0x0C + 0x00 through +0x09
```

They advance to the next record without reading or writing:

```text
0x02E8 + i*0x0C + 0x0A through +0x0B
```

The first padding pair is `0x02F2–0x02F3`; the final pair is `0x06CA–0x06CB`.

## Runtime preservation experiment

The full payload buffer was filled with three distinct values—`0xA5`, `0x5A`, and `0x3C`—before invoking the retail serializer. Results from serializer modes `0` and `1` were intersected so a coincidental matching output byte would not be treated as preserved.

The intersection contains exactly **176 untouched bytes**:

- payload `0x0000–0x0003`, which the caller later replaces with the checksum;
- payload `0x0054–0x0057`;
- payload `0x02E7`;
- all 83 two-byte record padding pairs;
- payload `0x1F5F`.

The inverse loop independently skips the same two bytes in every record. This makes the repeated record padding **confirmed serializer/deserializer padding**, not merely zero-looking storage.

The compact evidence is in `analysis/task8/payload-padding-evidence.json`. Full payload dumps remain ignored. The preservation analysis can be reproduced with:

```bash
python3 -m tools.gba.save_copy_map \
  --manifest analysis/runtime/task8/serializer-runs.json \
  --output analysis/runtime/task8/payload-preservation.json
```

## Task 8 custom-state storage

The existing `SU8C` slot is 64 bytes. The first 32 record padding pairs provide exactly 64 bytes:

```text
slot[2*i]     = payload[0x02E8 + i*0x0C + 0x0A]
slot[2*i + 1] = payload[0x02E8 + i*0x0C + 0x0B]
for i = 0..31
```

This maps the slot from payload `0x02F2` through sparse offset `0x0467`. The implementation is `src/custom_blader/payload_storage.py`.

Advantages over direct EEPROM-tail writes:

- the custom bytes are included in the retail payload checksum;
- the retail transaction already invalidates, programs, verifies, and commits the save;
- original saves naturally contain an invalid all-zero custom slot and load sanitized defaults;
- the original serializer and deserializer do not overwrite the mapped bytes;
- no new low-level EEPROM block protocol is required.

The EEPROM tail at blocks `0x3EF–0x3FF` remains unverified and native tail writes remain disabled. It is no longer required for Task 8 persistence.

## Remaining limits

The experiment proves the serializer/deserializer boundary. It does not yet prove that no unrelated high-level routine directly accesses the RAM payload padding. Native save/load hooks must therefore preserve the original order:

1. retail serializer;
2. custom-slot embedding;
3. retail checksum;
4. retail payload transaction.

On load, the custom slot must be extracted only after the retail payload has passed validation and the original deserializer has run. Runtime integration and repeated save/load tests remain required before this storage path can be called release-ready.

Other player, settings, play-time, money, inventory, story, tournament, durability, and progression fields remain unresolved unless separately identified by copy instructions or controlled comparisons.
