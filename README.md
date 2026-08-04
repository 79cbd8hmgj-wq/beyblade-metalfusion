# Beyblade G-Revolution Reverse Engineering

This repository contains reproducible tooling and documentation for reverse engineering **Beyblade G-Revolution (Game Boy Advance)**.

## GBA debugger bundle

The `Build GBA GDB Debugger Bundle` GitHub Action compiles a portable Linux x86_64 build of mGBA with its ARM GDB stub enabled. The resulting bundle provides:

- mGBA SDL frontend with ARMv4T debugging support
- GDB remote server on `127.0.0.1:2345`
- visible and headless launch scripts
- `gdb-multiarch` connection helper and initialization file
- captured build metadata, dependencies, help output, and SHA-256 checksums
- an automated smoke test that connects GDB to a generated minimal GBA test ROM

### Build manually

1. Open **Actions** in GitHub.
2. Select **Build GBA GDB Debugger Bundle**.
3. Choose **Run workflow**.
4. Leave `mGBA source ref` at the pinned default or supply another mGBA tag/commit.
5. Download the `mgba-linux-gdb-x86_64` artifact when the run completes.
6. Extract the downloaded ZIP, then extract `mgba-linux-gdb-x86_64.tar.xz`.

### Launch

```bash
./run-mgba-gdb.sh /path/to/game.gba
```

For a server without a visible emulator window:

```bash
./run-mgba-gdb-headless.sh /path/to/game.gba
```

Connect from another terminal:

```bash
./connect-gdb.sh
```

The repository and debugger artifact contain no commercial ROM, save file, or extracted copyrighted game asset.
