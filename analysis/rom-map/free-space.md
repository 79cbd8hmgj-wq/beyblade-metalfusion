# Free-space and expansion assessment

## Internal holes

The scan records 151 internal zero/`0xFF` runs of at least 256 bytes. All are **questionable**, not safe: direct aligned references and validated compression overlaps are counted, but ARM/Thumb branch coverage is not exhaustive. Exact ranges and neighbors are in `free-space.json`.

## Trailing padding

The final zero run is `0x003D52C0`–`0x00400000` (`0x083D52C0`–`0x08400000`), 175,488 bytes. It has 23 aligned pointer-like references and no validated LZ77 overlap. Consequently it remains **questionable**, despite being terminal fill; it is not approved patch space.

## Theoretical expansion

Expansion from 4 MiB to 8 MiB would add `0x00400000` bytes in the normal ROM address window. This is a **candidate engineering option**, not detected free space. Emulator/hardware compatibility, address decoding, save behavior, and all inserted references must be tested. No expanded ROM was written.
