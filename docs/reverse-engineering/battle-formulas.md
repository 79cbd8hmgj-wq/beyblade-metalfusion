# Original battle formulas

At runtime `0x080300D4`, type 0 selects `f10`, `f10 << 1`, or `f14` for moves
0, 1, or 2. Types 1 and 5 select `f14`, `f10 << 1`, or
`f14 + (f14 << 1)`. Type 2 returns an
arithmetic `f10 >> 1`. Type 3 returns `f10 + f14 + f18` only for move 3. Type 4
returns zero. Type 6 calls the existing RNG helper with bound four. Other cases
return zero. These instruction-derived paths are **confirmed**.

The helper uses 32-bit loads, additions, and shifts without saturation. The
exchange path later clamps signed negative intermediates before subtracting
from nested `+0x0C`. Full matchup semantics remain **strongly supported** until
runtime snapshots identify arguments and units. `tools.gba.battle_model`
preserves these branches and requires injected RNG.
