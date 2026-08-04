# Executable hooks

`hooks.py` encodes and decodes Thumb 16-bit `B`, Thumb `BL`, ARM `B`, and ARM `BL`, with signed displacement, PC bias, alignment, and edge-range validation. Long-range veneers use an explicit literal and preserve Thumb state. Call-site replacement requires exact original instruction bytes through `RomImage.write`. Arbitrary inline relocation is unsupported: branches, literal loads, PC-relative and mode-changing instructions are rejected. GNU ARM support is optional; install with `sudo apt-get install gcc-arm-none-eabi binutils-arm-none-eabi`. The raw-module path remains authoritative when absent.

Thumb veneers are accepted only at a 4-byte-aligned allocation so `ldr r3, [pc, #0]` addresses the following aligned literal. ARM jump veneers are supported; ARM call veneers are explicitly rejected because verified link-register/return preservation is not implemented.
