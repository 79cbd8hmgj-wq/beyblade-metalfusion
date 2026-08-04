# Tournament subsystem

Native Thumb routines are bounded in `analysis/scripts/function-map.json`.
`initTournament` begins at `0x0802C6AC`; `addTournamentPoints` at `0x0802C70C`;
`ResetTournament` at `0x0802CC58`; `ReInitTournament` at `0x0802CCC4`;
team/result helpers occupy `0x0802D144`–`0x0802D2C0`.

Direct instructions repeatedly load a runtime base through `0x03000198` and
access bytes/halfwords near offsets `0x15C8`–`0x15D2`. Halfwords at `+0x15D0`
and `+0x15D2` participate in signed comparisons and difference calculation,
so their score interpretation is **strongly supported**. Team IDs, round,
bracket, reward, and serialized location remain unknown. The reference model
covers u16 wrapping addition, comparison, tie, winner/loser, and absolute
point difference only.
