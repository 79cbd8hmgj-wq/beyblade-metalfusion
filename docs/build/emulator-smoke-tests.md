# Emulator smoke tests

Run `python3 -m tools.build.emulator_smoke BUILD.gba --mgba mgba --gdb gdb-multiarch`. The harness starts mGBA GDB mode at `127.0.0.1:2345`, waits boundedly, reads registers and PC, continues briefly, interrupts, checks liveness, issues `disconnect` (not `detach`), and terminates cleanly. When either binary/display support is absent it records the exact command as unexecuted rather than claiming a pass. Task 7 supplies no gameplay input.
