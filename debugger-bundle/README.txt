mGBA Linux x86_64 GDB debugger bundle
=====================================

This bundle is intended for Game Boy Advance reverse engineering. It contains
mGBA built with its ARM debugging infrastructure and remote GDB stub enabled.

Start with a visible emulator window:

  ./run-mgba-gdb.sh /path/to/game.gba

Start without video or audio devices:

  ./run-mgba-gdb-headless.sh /path/to/game.gba

The GDB server listens only on:

  127.0.0.1:2345

Connect from another terminal:

  ./connect-gdb.sh

The connection helper expects gdb-multiarch. On Debian/Ubuntu:

  sudo apt-get install gdb-multiarch

Manual GDB connection:

  gdb-multiarch
  (gdb) set architecture armv4t
  (gdb) target remote 127.0.0.1:2345

Useful commands:

  info registers
  x/16i $pc
  break *0x08000000
  watch *(unsigned int *)0x02000000
  continue
  stepi
  nexti
  detach

The GBA ROM is normally mapped beginning at 0x08000000. Convert a ROM file
offset to a runtime address by adding 0x08000000.

mGBA also supports its internal command-line debugger with the -d option, but
this package launches the remote GDB mode with -g by default.

No commercial ROM, save, extracted asset, or rebuilt game image is included.
The mGBA license is included as license.txt.
