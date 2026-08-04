# Custom Blader runtime-state foundation

## Implemented

`CustomBladerState` models schema version, initialization, player and Bey names, avatar/portrait/palette IDs, origin, tendency, dormant Blank Core overlay, component references, future flags, and a validation word. Sanitization clamps IDs, restores safe default names, and enforces dormant Blank Core state.

## Candidate

The Python byte layout is the candidate contract for future native layout generation.

## Unknown / unexecuted

No safe runtime allocation has been proven. No EWRAM address, heap allocation, or persistent player-structure spare bytes are claimed.
