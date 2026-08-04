# Persistent progression

`matchBladerExperience` (ROM `0x003A2D28`) and tournament/event names are code anchors, not proof of payload offsets. Story flags, money, shops, tournament points, wins/losses, experience, repair state and unlocks remain **unknown fields inside payload `0x0004–0x1F5F`**. This explicitly separates story/event candidates from temporary menu and battle-only state and defers opcode meanings to Task 6.

Recommended Task 6 entry anchors are references to `initTournament`, `addTournamentPoints`, `StartPrelim`, `StadiumEntry`, `TriggerBattle`, `atExitToStreets`, and `LockPoolDoors`; break at `0x08045198`/`0x08045590` to connect any modified runtime flag to persistence. No script interpreter reconstruction was undertaken.
