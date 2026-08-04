# Named event bindings

The word after each high-ROM identifier reference is a ROM data pointer. It is
therefore called a *stream target*, not a native callback. Confirmed bindings:
`atDojo` → `0x080B52E8`, `atExitToStreets` → `0x080B5310`, `inAlley` →
`0x080B3B70`, `LockPoolDoors` → `0x080A8368`, `StartPrelim` → `0x080AABEC`,
`StadiumEntry` → `0x080A8D7C`, and five instances of `TriggerBattle` →
`0x0809B350`.

Duplicate `TriggerBattle` entries are **strongly supported** as separate map
bindings to one reusable stream; they are not language copies because both the
identifier pointer and target are identical.
