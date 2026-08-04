# Serialized payload

The payload is exactly `0x1F60` bytes. Offset `0x0000` is its stored checksum. Coverage is `0x0004–0x1F5F`, interpreted as 2007 aligned little-endian 32-bit words with wrapping addition. Header `+0x04` duplicates the result; no secondary checksum was found (**strongly_supported**).

The serializer begins at `0x08045198`; the inverse begins at `0x08045590`. Static evidence bounds every remaining byte as an **unresolved copied/translated region**, rather than inventing names without controlled saves. Therefore player name, settings, play time, money, component bitfields/loadouts, story/tournament flags, durability and progression are currently **unknown at byte-field level**. They are persistent candidates because their runtime producers/consumers lead to this boundary, but Task 5 does not claim unsupported offsets. Temporary menus and battle-only state are excluded unless a copy instruction is demonstrated.

This conservative range map remains byte-complete and the parser preserves all unknown bytes. Exact next experiment: acquire baseline and single-property copied saves, run `python3 -m tools.gba.save_diff`, then break on the corresponding serializer read and deserializer write.
