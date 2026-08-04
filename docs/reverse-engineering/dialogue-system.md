# Dialogue and localization

Dialogue dispatch remains **candidate**. Action streams contain small integers
and ROM pointers, but static evidence gathered here does not safely distinguish
text IDs, speaker IDs, portraits, expressions, or choice results. No bulk text
was extracted. `dialogue_tables` supplies a byte-preserving tokenizer for
isolated control streams: NUL terminators, known synthetic two-byte controls
`0x01`–`0x03`, and all other control bytes survive round trip. These synthetic
rules are tooling contracts, not claims about retail meanings.

## Task 8 name-entry notes

**Confirmed anchors:** `Enter name` at ROM `0x003A3760`, localized pointer occurrence at `0x00096D00`, and candidate protagonist-name pointer table `0x00077F10-0x00077F20`. **Unknown:** destination buffer, maximum length, and semantic owner until runtime breaks/watchpoints are executed.
