# Save/load transactions

## Save pseudocode

```text
prepare_payload (0x08044E54): clear 0x1F60; serialize (0x08045198)
checksum (0x08044D8C): sum 2007 LE u32 words at +0x04..+0x1F5F modulo 2^32
store sum at payload +0; construct 24-byte header (0x08044EA0)
invalidate blocks 0..2 with zero blocks (0x08044F64)
program+verify blocks 3..0x3EE (0x08044F14; game retry ceiling 8)
program+verify blocks 0..2 last (0x08044D2C; game retry ceiling 8)
```

This is **strongly supported** header-last commit behavior. It detects power loss but has no redundant prior payload: invalidation destroys the old commit marker before payload replacement.

## Load pseudocode

```text
configure EEPROM with 0x40 (0x08044A8C -> 0x080674BC)
read blocks 0..2; reject bad magic or constant pairs
read blocks 3..0x3EE (0x08044FB0)
require header checksum == payload[0] == recomputed sum (0x080450E4)
deserialize (0x08045590) / activate (0x08045128)
on invalid constants, diagnostic path invalidates/erases header
```

The diagnostic strings at ROM `0x003A2E04` and `0x003A2E30` are direct binary anchors; whether output is visible in retail UI is **unknown**. Runtime corruption outcomes remain unclaimed and scripts are in `debugger-bundle/task5-save.gdb`.
