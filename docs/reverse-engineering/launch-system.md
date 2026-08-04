# Ripcord and launch system

The `initRipCord` diagnostic string at ROM `0x0033C77C` and its nearby pointer
reference at `0x0003B5BC` are **candidate** anchors. They do not establish the
function entry, state structure, timing windows, result scale, AI equivalence,
or stat handoff. Those remain **unknown**. The tracked GDB script supplies a
non-mutating starting point; weak, medium, and strong input recordings are
required before implementing a reference formula.
