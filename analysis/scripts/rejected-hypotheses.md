# Rejected and retained hypotheses

* **Rejected:** high identifier references point directly to native callbacks.
  Their targets begin aligned small u32 values and embedded pointers, not
  ARM/Thumb prologues.
* **Rejected:** every recurring u32 is already a proven opcode. Recurrence does
  not separate opcode from operand; values stay neutral.
* **Rejected:** low small integers are coordinates or entity types merely due
  to range. No runtime consumer establishes those semantics.
* **Rejected:** five `TriggerBattle` references are five implementations. All
  resolve to `0x0809B350`.
* **Retained candidate:** low inline-name records are authored map/event
  definitions mirrored by the high binding layer.
* **Unknown:** conventional bytecode call stack, concurrency, and per-script
  context layout.
