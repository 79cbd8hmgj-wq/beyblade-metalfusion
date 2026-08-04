# Important string clusters

These are **confirmed direct string locations**; meanings beyond identifier spelling are structural inference.

* Tournament identifiers cluster around `0x0033BE50` (`0x0833BE50`): `initTournament`; `addTournamentPoints` is at `0x0033BE7C`; `getWinningTeam` at `0x0033BF24`; `getLosingTeam` at `0x0033BF34`; and `getPointsDifference` at `0x0033BF70`.
* Battle/menu identifiers cluster around `0x0033C274`–`0x0033C77C`: `updateAttackHold`, `initBattleOverlays`, `drawSelectMoveMenu`, and `initRipCord`.
* Collection identifiers cluster around `0x0033D1C4`–`0x0033D358`: `getRandomBeyBladeFromSeason`, `getBeyBladeWithIndex`, and `removeBladeFromTysonsCollection`.
* `initBeybladeMenu` is separate at `0x003A8990` / `0x083A8990`.

Case-insensitive anchor matching found all thirteen requested names. Nearby printable runs are not assumed to be callable symbol tables without runtime references.
