# Component stat aggregation (Task 3 boundary)

No static candidate met the repository's threshold for naming a complete stat
aggregation formula. This result is **unknown**, not a claim that aggregation
does not exist. The confirmed template accessor at ROM `0x0003DCFC` returns the
40-byte template, while Task 3 establishes category-ID bytes at `+0x1D`,
`+0x1E`, `+0x20`, and `+0x21`; no direct code-read chain from all four name
arrays into a common destination was confirmed.

The exact next experiment is to break at runtime `0x0803DCFC`, open the
customization screen, finish the call, and set read watchpoints on returned
pointer offsets `+0x1C..+0x23`. Record the PC, registers, and destination RAM
before and after changing exactly one component. This separates menu display
aggregation from battle-effective aggregation without beginning Task 4.

