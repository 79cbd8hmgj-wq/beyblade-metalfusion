# Concrete unresolved questions

* Which code references or emits the identifier pools at `0x0033BE50`–`0x0033D358`, and are these debug symbols, script command names, or registration records?
* What are the entry count and field meanings of the candidate pointer run at `0x00000AA0` and higher-ranked runs in `analysis/pointers/table-candidates.json`?
* Which of the 226 structurally valid LZ77 streams are graphics, maps, audio, or general data? Runtime decompression destinations are required; plausible Huffman/RLE/differential headers also need format-specific validation.
* Where exactly do ARM bootstrap code, Thumb game code, literal pools, and non-code data transition? Static density is insufficient for instruction-accurate boundaries.
* Does `EEPROM_V` at `0x003A937C` belong to a versioned EEPROM library whose suffix is stored non-contiguously, and what code range implements it?
* Do any unaligned, computed, or encoded pointers enter the terminal fill at `0x003D52C0`? Twenty-three aligned pointer-like words already target it.
* Which candidate tables encode Beyblade records? This is intentionally deferred to Task 2 and requires watchpoints/breakpoints rather than semantic guessing.
