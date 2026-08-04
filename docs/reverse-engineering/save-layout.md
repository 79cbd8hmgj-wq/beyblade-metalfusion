# Physical save layout

**Strongly supported capacity:** one 8-KiB EEPROM image. This is one transaction, not multiple user-visible slots.

| Blocks | EEPROM bytes | Length | Classification | Confidence |
|---|---:|---:|---|---|
| `0x000–0x002` | `0x0000–0x0017` | `0x18` | transaction header | confirmed |
| `0x003–0x3EE` | `0x0018–0x1F77` | `0x1F60` | serialized payload | confirmed |
| `0x3EF–0x3FF` | `0x1F78–0x1FFF` | `0x88` | unreferenced tail, **not proven free** | strongly_supported |

All direct game callers found stay within these ranges. Computed payload block `3+i` has `0 <= i < 1004`. No identified producer accesses the tail, but indirect access is not disproven; expansion there is **questionable**, never safe merely because bytes are zero.

## Task 8 custom extension candidate

**Strongly supported but not dynamically confirmed:** the high-level payload loops end at block `0x3EE`; Task 8 tooling models tail blocks `0x3EF-0x3FE` as two transaction slots and leaves block `0x3FF` reserved. Dynamic watchpoint proof remains required before native ROM writes are enabled.
