# Task 6 evidence ledger

* **confirmed / direct binary:** supported ROM SHA-256 is
  `c4a568adc896bace0e25dbff4aa0c1802933c88e3f4a4e825075116c8c4173e5`.
* **confirmed / direct binary:** high binding offsets and targets are in
  `callback-registry.json`; every target normalizes inside the 4 MiB ROM.
* **strongly_supported / inference from instruction bytes:** the targets are
  aligned word streams, not executable entry points.
* **confirmed / direct binary:** tournament identifier literals occur in Thumb
  functions bounded in `function-map.json`.
* **strongly_supported / static data flow:** tournament score comparisons use
  halfwords at runtime-base-relative `0x15D0` and `0x15D2`.
* **unknown:** no dynamic experiment ran and no persistence payload field is
  promoted.
