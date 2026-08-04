# Deterministic build system

**confirmed infrastructure:** `python3 -m tools.build.build_rom` is the authoritative path. It opens the supported 4 MiB ROM read-only, verifies SHA-256 `c4a568adc896bace0e25dbff4aa0c1802933c88e3f4a4e825075116c8c4173e5`, builds in memory, checks source integrity, and atomically replaces output only under the selected ignored directory. It refuses a source/output path collision.

```sh
./scripts/build-spirit-unbound.sh "Beyblade G-Revolution (USA).gba" infrastructure-smoke
```

The pipeline loads a dependency-checked profile, expands, allocates, loads resources, performs guarded writes, emits metadata, validates, writes a ROM, creates and reapplies BPS, and emits deterministic audit artifacts. No timestamp, host path, user, hostname, UUID, or directory enumeration enters output. Recovery is a clean rebuild; generated ROMs are never edited.

## Integration status

The authoritative builder **integrates** guarded patch kinds, conservative string pools and explicit pointer rows, confirmed validate-only retail table round trips, explicit-site pointer relocation, checked ARM/Thumb branch hooks, raw/hex modules, metadata, BPS verification, central validation, manifests, and optional emulator smoke execution. Compiled GNU ARM modules are an implemented utility but are not accepted as a profile operation yet; profiles must use a raw or hex module. Retail table mutation/relocation and fixed-table relocation are unsupported without complete consumer bounds and are explicitly rejected. Emulator execution is optional and is recorded as `unexecuted`, never passed, when external tools are absent.
