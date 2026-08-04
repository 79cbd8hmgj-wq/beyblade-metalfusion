# Pointer evidence

The aligned scan found 48,159 range-valid words, including 35,810 ROM targets. This is **confirmed syntax**, not confirmed semantics. It identified 1,341 consecutive runs of three or more candidates.

Representative **candidate** runs begin at `0x0000024C` (six mixed ROM/IWRAM targets), `0x00000558` (four ROM targets), and `0x00000AA0` (ten ROM targets). Ranked records preserve target distributions, uniqueness, evidence, and counterevidence in `table-candidates.json`. Fixed-stride structures beyond stride four and string/function-table semantics require dynamic access evidence, so they remain unresolved rather than being over-labelled.
