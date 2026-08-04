# Runtime battle state

The participant has a **strongly supported** minimum accessed extent of `0x310`:
`+0x04` nested pointer, `+0x2C8` move word, `+0x2CC` type word, and `+0x30C`
byte identifier candidate. `+0x2B8` is an accumulator/effect candidate.

The nested object has a supported minimum extent of `0x1C`. Word `+0x0C` is a
mutable battle quantity, while `+0x10`, `+0x14`, and `+0x18` are effective
selector inputs. Stat names, units, and unsignedness are **unknown**; the
resolver performs signed comparisons. The controller, animation, launch, AI,
and result ownership boundaries remain unknown. Machine-readable access widths
and confidence are in `analysis/battle/battle-state.json`.
