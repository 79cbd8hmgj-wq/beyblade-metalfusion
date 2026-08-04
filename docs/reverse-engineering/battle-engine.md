# Task 4 battle-engine reconstruction

All findings use `confirmed`, `strongly_supported`, `candidate`, or `unknown`.
ROM offsets below convert to runtime addresses by adding `0x08000000`.

## Architecture and command flow

The **strongly supported** participant object owns a nested runtime Bey pointer
at `+0x04`, a move word at `+0x2C8`, and a type word at `+0x2CC`. A diagnostic
function at ROM `0x0002FF48` indexes the two name tables at `0x00077F44` and
`0x00077F24` with those words. The value selector at `0x000300D4` independently
dispatches on `+0x2CC`, reads `+0x2C8`, and consumes three assembled values.

The resulting supported lifecycle is: menu/AI producer (**unknown**) writes the
shared selectors; preparation/animation (**candidate**) runs; the selector
computes an exchange value; `0x0002FFAC` applies exchange special cases, clamps
negative residuals, updates the nested mutable word, writes paired outcome codes,
and calls post-resolution helpers. This supports a later resolver hook at
`0x0802FFAC`, with `0x080300D4` as the narrower value-policy hook. Neither is a
safe patch specification yet.

## Enums and function map

Move values `0..6` are Attack, Defense, Endurance, Bit Beast, Bit Beast Target,
Jump, and Dodge. Type values `0..7` are Attack, Defend, Combo, Bit Beast, Other,
Idle, Combo Target, and Hurt. Labels are **confirmed** strings; correspondence
to gameplay words is **strongly supported**, not runtime-confirmed. See
[`enum-map.json`](../../analysis/battle/enum-map.json) and
[`function-map.json`](../../analysis/battle/function-map.json).

## Subsystem boundaries

* Stat assembly is **unknown**: the selector sees post-assembly words, not part
  IDs. No displayed-stat equivalence is claimed.
* Bit Beast mechanics and presentation are distinct. Type 3/move 3 selects the
  sum of the three runtime words; no 32-row presentation mapping is inferred.
* Packed core bit `0x40` is **strongly supported** as a behavior branch at
  `0x08030316`; “Engine Gear” remains only a candidate semantic name.
* `initBattleOverlays`, `drawSelectMoveMenu`, and `initRipCord` strings provide
  **candidate** presentation/lifecycle boundaries, not confirmed formulas.
* AI profiles, launch arithmetic, effect dispatch, and story/tournament handoff
  remain **unknown** rather than invented.

## Runtime evidence and regeneration

No GDB endpoint was running with a reproducible battle-ready state. Therefore
there is no claimed runtime evidence. `debugger-bundle/task4-battle.gdb` records
the exact priority breakpoints and fields without modifying ROM. Regenerate
compact ignored data with:

```sh
python3 -m tools.gba.battle_enums --rom "Beyblade G-Revolution (USA).gba" --output analysis/generated/battle-enums.json
python3 -m tools.gba.battle_functions --rom "Beyblade G-Revolution (USA).gba" --output analysis/generated/battle-functions.json
```

## Exact unresolved experiments

Reach a normal battle, correlate every menu choice at `0x0802FF48`, capture
Attack/Attack and Attack/Defense before/after snapshots at `0x0802FFAC`, vary one
component at `0x080300D4`, compare templates across the `0x40` branch, and trace
weak/medium/strong launch results from the true `initRipCord` implementation.
Repeat identical AI states to separate deterministic choice from RNG.
