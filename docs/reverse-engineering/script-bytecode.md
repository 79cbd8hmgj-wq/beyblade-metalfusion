# Event action words

**Strongly supported:** named targets are aligned little-endian 32-bit word
streams. **Unknown:** whether each word is an opcode, operand, tagged action, or
part of a variable-size record. Representative values include `0x04`, `0x0E`,
`0x0F`, `0x11`, `0x16`, and `0xCF`. `0x16` is followed by ROM pointers in several
streams, but is only a pointer-bearing-command **candidate**.

`event_records.decode_words` and `encode_words` are intentionally lossless.
Unknown words, pointer-looking values, and padding survive byte-for-byte. A
semantic assembler is not claimed before the dispatcher is bounded.
