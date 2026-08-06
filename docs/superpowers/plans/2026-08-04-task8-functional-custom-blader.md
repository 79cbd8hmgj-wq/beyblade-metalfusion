# Functional Task 8 Custom Blader Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert the merged Task 8 foundation into a functional, deterministic GBA patch that enters a Tier-A Custom Blader creator from New Game, persists identity safely, substitutes the protagonist name, selects verified player presentation resources, grants evidence-backed starters, and preserves a dormant Blank Core identity.

**Architecture:** Keep the Python models as the specification and add an evidence-first native layer. Runtime analysis produces guarded hook descriptors and resource manifests; generated ARM/Thumb modules live in expansion ROM and expose a compact ABI for creator state, name lookup, save extension, player presentation, starter initialization, and Blank Core behavior. The release profile remains disabled for any subsystem whose hook or storage safety is not proven, while dedicated research profiles and GDB scripts collect the missing evidence without weakening build-system guarantees.

**Tech Stack:** Python 3 standard library, existing `tools.build` pipeline, ARM7TDMI Thumb/ARM assembly, optional `arm-none-eabi-*` verification, mGBA GDB remote debugging, BPS patch generation, JSON schemas and manifests.

## Global Constraints

- Supported source ROM SHA-256 is `c4a568adc896bace0e25dbff4aa0c1802933c88e3f4a4e825075116c8c4173e5`.
- The source ROM is immutable and must never be committed or modified in place.
- Every original-ROM write requires exact expected bytes.
- Every new code or data allocation has a stable ID and uses expansion ROM by default.
- No tracked binary fixture is allowed; generated module bytes are stored as lowercase text hex with decoded-byte hashes.
- No commercial asset bytes are committed. Existing graphics are referenced by source-ROM range or pointer and copied only during the build.
- EEPROM tail blocks `0x3EF–0x3FF` remain experimental until dynamic access tracing proves they are unused by the original game.
- Unknown ROM semantics remain classified as `unknown` or `candidate`; implementation cannot promote confidence without evidence.
- Two independent clean builds must produce byte-identical ROM, BPS, manifest, allocation map, hooks, relocations, module report, and human report.
- A functional subsystem is not documented as implemented until its native hook is present and its runtime test is executed.

---

## File Structure

### Runtime-analysis and evidence

- Create: `tools/gba/task8_static.py` — focused scanner for New Game, name-entry, protagonist lookup, player actor, portrait, inventory, and Bit Chip consumer anchors.
- Create: `tools/gba/task8_trace.py` — parses compact GDB logs into stable evidence JSON.
- Create: `analysis/task8/hook-candidates.json` — exact guarded candidate sites and confidence.
- Create: `analysis/task8/resource-candidates.json` — avatar, portrait, palette, and starter candidates with evidence.
- Create: `analysis/task8/eeprom-tail-evidence.json` — block-access and preservation evidence.
- Create: `debugger-bundle/task8-name-entry.gdb`.
- Create: `debugger-bundle/task8-new-game.gdb`.
- Create: `debugger-bundle/task8-eeprom-tail.gdb`.
- Create: `debugger-bundle/task8-player-assets.gdb`.
- Create: `debugger-bundle/task8-blank-core.gdb`.

### Native module source and generated layout

- Create: `src/native/task8/custom_state.h`.
- Create: `src/native/task8/custom_state.c`.
- Create: `src/native/task8/custom_save.h`.
- Create: `src/native/task8/custom_save.c`.
- Create: `src/native/task8/creator.h`.
- Create: `src/native/task8/creator.c`.
- Create: `src/native/task8/name_render.h`.
- Create: `src/native/task8/name_render.c`.
- Create: `src/native/task8/player_assets.h`.
- Create: `src/native/task8/player_assets.c`.
- Create: `src/native/task8/starter.h`.
- Create: `src/native/task8/starter.c`.
- Create: `src/native/task8/blank_core.h`.
- Create: `src/native/task8/blank_core.c`.
- Create: `src/native/task8/task8_hooks.S`.
- Create: `src/native/task8/task8.ld.in`.
- Create: `data/build/fixtures/task8-native.hex` — generated lowercase hex after verified compilation.
- Create: `data/build/fixtures/task8-native.sha256` — decoded-byte SHA-256 and toolchain provenance.

### Build and data integration

- Modify: `tools/build/toolchain.py` — deterministic Task 8 module build and symbol export.
- Modify: `tools/build/modules.py` — symbol-aware checked hex module loading.
- Modify: `tools/build/build_rom.py` — source-range assets and symbol-targeted hooks/relocations.
- Modify: `tools/build/profile.py` — strict validation for Task 8 operation kinds.
- Create: `data/custom_blader/state-layout.json`.
- Replace: `data/custom_blader/assets.json` with verified source-ROM references.
- Replace: `data/custom_blader/origins.json` with evidence-backed starter records.
- Create: `data/custom_blader/creator-options.json`.
- Create: `data/custom_blader/name-substitution.json`.
- Create: `data/custom_blader/blank-core.json`.
- Replace: `data/build/profiles/custom-blader-foundation.json` with a functional profile once all required gates pass.
- Create: `data/build/profiles/task8-research.json` for non-release debug hooks.

### Python/native contract and save tools

- Modify: `src/custom_blader/custom_state.py`.
- Modify: `src/custom_blader/custom_save.py`.
- Modify: `src/custom_blader/creator_menu.py`.
- Modify: `src/custom_blader/name_render.py`.
- Create: `src/custom_blader/native_layout.py`.
- Modify: `tools/gba/custom_save_extension.py`.
- Modify: `tools/gba/save_format.py`.
- Modify: `tools/gba/save_diff.py`.

### Tests and documentation

- Create: `tests/custom_blader/test_native_layout.py`.
- Create: `tests/custom_blader/test_task8_static.py`.
- Create: `tests/custom_blader/test_task8_profile.py`.
- Create: `tests/custom_blader/test_custom_save_transactions.py`.
- Create: `tests/custom_blader/test_creator_state_machine.py`.
- Create: `tests/custom_blader/test_name_substitution.py`.
- Create: `tests/custom_blader/test_resource_manifests.py`.
- Create: `tests/custom_blader/test_blank_core.py`.
- Modify: `tests/custom_blader/test_task8_models.py`.
- Update: strict Task 8 schemas under `schemas/`.
- Update: Task 8 implementation and reverse-engineering reports under `docs/implementation/` and `docs/reverse-engineering/`.

---

### Task 1: Lock the Python/native state and save contract

**Files:**
- Modify: `src/custom_blader/custom_state.py`
- Modify: `src/custom_blader/custom_save.py`
- Create: `src/custom_blader/native_layout.py`
- Create: `data/custom_blader/state-layout.json`
- Create: `tests/custom_blader/test_native_layout.py`
- Create: `tests/custom_blader/test_custom_save_transactions.py`

**Interfaces:**
- Consumes: current `CustomBladerState`, `serialize_slot`, `parse_slot`, `select_newest`.
- Produces: `STATE_SIZE`, `STATE_OFFSETS`, `SLOT_LAYOUT`, `serialize_state_bytes(state) -> bytes`, `parse_state_bytes(raw) -> CustomBladerState`, `simulate_slot_transaction(old_a, old_b, state, interrupt_after_block) -> tuple[bytes, bytes]`.

- [ ] **Step 1: Write failing distinct-field layout tests**

Create tests that assign unique nonzero values to every persisted field, serialize the state and slot, parse both, and assert exact field equality. Assert fixed offsets and exact total sizes.

- [ ] **Step 2: Run focused tests and confirm the missing native-layout API fails**

Run `python3 -m unittest tests.custom_blader.test_native_layout -v`.

- [ ] **Step 3: Implement explicit layout constants and byte serializers**

Use named offsets only; reject positional persisted constructors. Define one canonical layout consumed by Python tests and emitted as C macros.

- [ ] **Step 4: Add transaction interruption tests**

Simulate interruption before each EEPROM block write, before commit, after commit, and after verification. Assert loading returns either the previous complete state or the new complete state, never a mixed state.

- [ ] **Step 5: Fix sequence ambiguity and validation behavior**

Define the exact result when sequence difference equals `0x80000000`, when schemas are newer, when validation words disagree, and when both slots are invalid.

- [ ] **Step 6: Run all custom-state/save tests**

Run `python3 -m unittest discover -s tests/custom_blader -v`.

- [ ] **Step 7: Commit**

Commit message: `test: lock Task 8 state and save contracts`.

---

### Task 2: Build focused static-analysis tooling and candidate reports

**Files:**
- Create: `tools/gba/task8_static.py`
- Create: `analysis/task8/hook-candidates.json`
- Create: `analysis/task8/resource-candidates.json`
- Create: `tests/custom_blader/test_task8_static.py`
- Update: `docs/reverse-engineering/dialogue-system.md`
- Update: `docs/reverse-engineering/map-and-entity-data.md`
- Update: `docs/reverse-engineering/component-tables.md`

**Interfaces:**
- Consumes: supported ROM bytes, existing address helpers, Thumb scanner, string/pointer reports.
- Produces: `scan_task8(rom: bytes) -> dict`, stable candidate IDs, exact offsets, expected bytes, xrefs, confidence, and next breakpoint.

- [ ] **Step 1: Write synthetic scanner tests**

Test literal-reference discovery, Thumb function-boundary candidates, pointer-row consumers, guarded byte extraction, and deterministic JSON ordering.

- [ ] **Step 2: Implement anchor and xref scans**

Scan `NEW GAME` at `0x003A3150`, `Name:` at `0x003A34F0`, `Enter name` at `0x003A3760`, localized pointer row near `0x00096D00`, protagonist row `0x00077F10–0x00077F20`, save functions, complete-template `+0x21` reads, and inventory/equip functions.

- [ ] **Step 3: Add instruction-context summaries**

For each xref, retain a compact instruction window and neutral function candidate; do not assign semantic names from strings alone.

- [ ] **Step 4: Run against the supported ROM**

Generate ignored full output and tracked compact candidate reports. Verify the ROM hash before and after.

- [ ] **Step 5: Document confirmed anchors and unresolved consumers**

Update reports with exact evidence and confidence.

- [ ] **Step 6: Commit**

Commit message: `analysis: map Task 8 native hook candidates`.

---

### Task 3: Establish reproducible mGBA runtime evidence

**Files:**
- Create: `tools/gba/task8_trace.py`
- Create: `debugger-bundle/task8-name-entry.gdb`
- Create: `debugger-bundle/task8-new-game.gdb`
- Create: `debugger-bundle/task8-eeprom-tail.gdb`
- Create: `debugger-bundle/task8-player-assets.gdb`
- Create: `debugger-bundle/task8-blank-core.gdb`
- Create: `analysis/task8/eeprom-tail-evidence.json`
- Create: `tests/custom_blader/test_task8_trace.py`

**Interfaces:**
- Consumes: mGBA GDB endpoint `127.0.0.1:2345`, compact log format.
- Produces: normalized evidence events `{experiment, breakpoint, registers, memory, conclusion, confidence}`.

- [ ] **Step 1: Write parser tests from synthetic GDB transcripts**

Cover breakpoint hits, register captures, memory dumps, EEPROM block indices, no-hit runs, and malformed lines.

- [ ] **Step 2: Implement bounded GDB command files**

Each script must set exact breakpoints, log machine-readable markers, avoid `detach`, use `disconnect`, and terminate cleanly.

- [ ] **Step 3: Acquire and unpack the verified mGBA bundle**

Use the latest successful GitHub Actions artifact when available. Verify checksums and executable dependencies.

- [ ] **Step 4: Run EEPROM-tail access tracing**

Exercise blank boot, valid-save boot, New Game, save/load, component changes, battle completion, tournament result, and settings changes. Seed a copied tail pattern and verify at least three original save cycles.

- [ ] **Step 5: Run name-entry and New Game traces**

Record destination buffer, length, encoding, state transitions, caller, and return path.

- [ ] **Step 6: Run player-resource and Bit Chip traces**

Record player actor resource selection, portrait consumers, palette upload, complete-template `+0x21` reads, name lookup, move lookup, and removal/sale paths.

- [ ] **Step 7: Generate compact evidence reports**

Promote confidence only for executed observations. If a path cannot be triggered, retain the exact unexecuted command and required state.

- [ ] **Step 8: Commit**

Commit message: `analysis: add Task 8 runtime evidence harness`.

---

### Task 4: Add deterministic native module compilation and ABI verification

**Files:**
- Modify: `tools/build/toolchain.py`
- Modify: `tools/build/modules.py`
- Modify: `tools/build/profile.py`
- Create: `src/native/task8/task8.ld.in`
- Create: `src/native/task8/custom_state.h`
- Create: `src/native/task8/custom_state.c`
- Create: `src/native/task8/task8_hooks.S`
- Create: `data/build/fixtures/task8-native.hex`
- Create: `data/build/fixtures/task8-native.sha256`
- Create: `tests/custom_blader/test_task8_profile.py`

**Interfaces:**
- Consumes: generated state-layout macros and expansion allocation address.
- Produces: deterministic linked module, symbol map, text-safe hex, decoded-byte SHA-256, and profile symbol references.

- [ ] **Step 1: Write toolchain contract tests**

Test source ordering, linker-address substitution, symbol-map parsing, checked-hex fallback, decoded hash validation, and absent-toolchain reporting.

- [ ] **Step 2: Implement source-to-module build command**

Compile for `arm7tdmi`, Thumb interworking, freestanding mode, no host paths, no build IDs, and deterministic object order.

- [ ] **Step 3: Implement native state default/sanitize/accessors**

Match Python byte layout exactly and expose stable symbols.

- [ ] **Step 4: Add cross-language ABI verification**

When toolchain exists, compile a small layout probe or inspect exported constants and compare every offset and size to Python.

- [ ] **Step 5: Generate and verify checked text hex**

Never commit raw binary. Store exact decoded-byte hash and tool versions.

- [ ] **Step 6: Commit**

Commit message: `build: add deterministic Task 8 native module`.

---

### Task 5: Implement native custom save integration after storage proof

**Files:**
- Create: `src/native/task8/custom_save.h`
- Create: `src/native/task8/custom_save.c`
- Modify: `src/native/task8/task8_hooks.S`
- Modify: `tools/gba/custom_save_extension.py`
- Modify: `data/build/profiles/task8-research.json`
- Create: `tests/custom_blader/test_native_save_contract.py`

**Interfaces:**
- Consumes: proven EEPROM block API addresses and `eeprom-tail-evidence.json`.
- Produces: `Task8_LoadCustomState`, `Task8_SaveCustomState`, `Task8_ResetCustomState`, guarded load/save hooks, and exact slot transaction behavior.

- [ ] **Step 1: Gate implementation on evidence**

The build must refuse native EEPROM-tail hooks unless evidence status is `confirmed`, the observed original block maximum is `0x3EE`, and seeded-tail preservation tests passed.

- [ ] **Step 2: Write native/Python checksum and slot-vector tests**

Use fixed vectors covering valid, bad CRC, missing commit, older/newer sequence, and wraparound.

- [ ] **Step 3: Implement EEPROM read/write wrappers**

Call the original verified EEPROM_V124 functions and preserve calling convention and registers.

- [ ] **Step 4: Implement load and save transactions**

Read both slots, select newest, sanitize, write inactive slot data first and commit last, verify each block, and retain the old slot on failure.

- [ ] **Step 5: Hook original load/save success paths**

Use exact guarded instructions and preserve original return behavior. Original save validity remains authoritative.

- [ ] **Step 6: Test migration and stale-extension clearing**

Original valid save without extension gets defaults; invalid original save does not inherit stale custom identity.

- [ ] **Step 7: Commit**

Commit message: `feat: persist custom Blader state transactionally`.

---

### Task 6: Implement the native creator and New Game interception

**Files:**
- Create: `src/native/task8/creator.h`
- Create: `src/native/task8/creator.c`
- Modify: `src/native/task8/task8_hooks.S`
- Modify: `src/custom_blader/creator_menu.py`
- Create: `data/custom_blader/creator-options.json`
- Create: `tests/custom_blader/test_creator_state_machine.py`

**Interfaces:**
- Consumes: verified original name-entry/menu functions and runtime state accessors.
- Produces: `Task8_CreatorInit`, `Task8_CreatorUpdate`, `Task8_CreatorDraw`, `Task8_CreatorCommit`, and guarded New Game hook.

- [ ] **Step 1: Expand Python state-machine tests**

Test every forward/back/cancel transition, retention of prior choices, invalid IDs, summary, existing-save bypass, and final confirmation.

- [ ] **Step 2: Define compact creator option tables**

Use stable IDs, localized labels, descriptions, resource references, compatibility lists, and defaults.

- [ ] **Step 3: Reuse verified name-entry component**

Wrap the original keyboard for player and Bey names with bounded buffers and safe cancel behavior.

- [ ] **Step 4: Implement appearance/origin/tendency screens**

Use existing cursor, input, text, and preview primitives. Fallback resources are mandatory.

- [ ] **Step 5: Hook New Game after confirmation and before starter initialization**

Existing save/load paths must never enter the creator.

- [ ] **Step 6: Run creator runtime matrix**

Complete, backtrack, cancel, restart, and invalid-option tests in mGBA. Record no-soft-lock evidence.

- [ ] **Step 7: Commit**

Commit message: `feat: add Tier-A Custom Blader creator`.

---

### Task 7: Implement token-aware player/Bey name rendering

**Files:**
- Create: `src/native/task8/name_render.h`
- Create: `src/native/task8/name_render.c`
- Modify: `src/native/task8/task8_hooks.S`
- Modify: `src/custom_blader/name_render.py`
- Create: `data/custom_blader/name-substitution.json`
- Create: `tests/custom_blader/test_name_substitution.py`

**Interfaces:**
- Consumes: verified protagonist lookup/formatter sites and runtime state.
- Produces: bounded custom-name lookup, uppercase lookup, custom Bey-name lookup, intentional-NPC bypass, and coverage report.

- [ ] **Step 1: Write boundary-aware substitution tests**

Cover exact tokens, uppercase, punctuation, possessives, embedded false positives, invalid state fallback, truncated destination, and intentional-NPC contexts.

- [ ] **Step 2: Implement lookup-aware native substitution**

Prefer protagonist-name ID redirection over scanning arbitrary rendered text. Use bounded temporary buffers only where necessary.

- [ ] **Step 3: Hook verified UI systems**

Dialogue, menu/profile, HUD, tournament, result, and save/load display paths receive explicit site records.

- [ ] **Step 4: Generate remaining-fixed-name report**

Classify each Tyson/Takao occurrence as substituted, intentional character, debug-only, or unresolved.

- [ ] **Step 5: Run runtime rendering tests**

Use short, maximum-length, mixed-case, and punctuation-heavy valid names.

- [ ] **Step 6: Commit**

Commit message: `feat: render persistent custom Blader names`.

---

### Task 8: Implement verified avatars, portraits, palettes, origins, and starters

**Files:**
- Create: `src/native/task8/player_assets.h`
- Create: `src/native/task8/player_assets.c`
- Create: `src/native/task8/starter.h`
- Create: `src/native/task8/starter.c`
- Modify: `src/native/task8/task8_hooks.S`
- Replace: `data/custom_blader/assets.json`
- Replace: `data/custom_blader/origins.json`
- Create: `tests/custom_blader/test_resource_manifests.py`

**Interfaces:**
- Consumes: verified player actor/portrait/palette hooks, complete-template table, inventory/equip functions.
- Produces: source-ROM resource manifests, player-only asset lookup, four origin starter records, and one-time starter grant.

- [ ] **Step 1: Replace placeholder asset entries with exact references**

Every avatar and portrait records source pointer/range, dimensions, palette, frame compatibility, consumers, and evidence.

- [ ] **Step 2: Add manifest compatibility tests**

Reject missing directions, incompatible portrait/avatar pairs, out-of-range palettes, shared-NPC mutation, and unproven resources.

- [ ] **Step 3: Hook player-only asset selection**

NPC resource lookups remain unchanged. Copy-on-build or runtime pointer override must not mutate shared source records.

- [ ] **Step 4: Derive evidence-backed starters**

Use actual component IDs and type/stat evidence; do not map origins to template IDs `0–3` by position.

- [ ] **Step 5: Implement one-time starter grant**

Initialize active build and owned parts without duplicate rewards during migration or subsequent loads.

- [ ] **Step 6: Run all-direction and presentation tests**

Walk, interact, dialogue, profile, battle, and result paths for each verified option.

- [ ] **Step 7: Commit**

Commit message: `feat: add verified Custom Blader presentation and starters`.

---

### Task 9: Implement dormant Blank Core overlay and invariants

**Files:**
- Create: `src/native/task8/blank_core.h`
- Create: `src/native/task8/blank_core.c`
- Modify: `src/native/task8/task8_hooks.S`
- Create: `data/custom_blader/blank-core.json`
- Create: `tests/custom_blader/test_blank_core.py`

**Interfaces:**
- Consumes: verified Bit Chip name, inventory, equip, sell/remove, battle setup, Bit Beast, and Special Move consumers.
- Produces: dormant identity overlay that keeps retail mechanics on a valid neutral Bit Chip while exposing Blank Core player-facing identity.

- [ ] **Step 1: Write invariant tests**

Assert owned, active, persistent, non-removable, no Bit Beast, no Special Move, safe battle setup, and survival across physical-part changes.

- [ ] **Step 2: Choose the evidence-backed architecture**

Prefer identity overlay unless all retail consumers can safely accept an expanded ID. Record the neutral retail Bit Chip used internally and why it grants no move.

- [ ] **Step 3: Hook player-facing identity and removal paths**

Name and menu paths show Blank Core; sell/remove/discard reject it; opponent paths are unchanged.

- [ ] **Step 4: Suppress Spirit/Bit Beast presentation**

Dormant state must not resolve to an existing presentation pair, sound, move, or AI action.

- [ ] **Step 5: Run save/load and customization runtime tests**

Change each of the other four parts, save, load, enter battle, and attempt every removal path.

- [ ] **Step 6: Commit**

Commit message: `feat: add persistent dormant Blank Core overlay`.

---

### Task 10: Convert the foundation profile into the functional release profile

**Files:**
- Replace: `data/build/profiles/custom-blader-foundation.json`
- Modify: `tools/build/build_rom.py`
- Modify: `tools/build/validation.py`
- Modify: strict Task 8 schemas under `schemas/`
- Create: `tests/custom_blader/test_task8_profile.py`
- Update: `README.md`
- Update: all Task 8 implementation reports

**Interfaces:**
- Consumes: all verified native modules, hooks, resources, text, save evidence, and manifests.
- Produces: deterministic 8-MiB functional ROM, verified BPS, complete audit manifest, and runtime acceptance report.

- [ ] **Step 1: Require non-empty functional operations**

The profile must include creator, save, name, asset, starter, and Blank Core modules/hooks. Validation rejects the former metadata-only foundation shape.

- [ ] **Step 2: Strengthen strict schemas**

Use concrete fields, `additionalProperties: false`, ID bounds, strict hex patterns, resource compatibility, evidence references, and confidence enums.

- [ ] **Step 3: Build twice and compare deterministic artifacts**

Compare ROM, BPS, manifest, allocation map, changed ranges, hooks, relocations, modules, assets, tables, texts, validation, and report byte-for-byte.

- [ ] **Step 4: Apply BPS and verify exact reconstruction**

Verify source and target hashes and preserve the source ROM unchanged.

- [ ] **Step 5: Execute complete mGBA acceptance suite**

Creator entry/completion, names, assets, origins/starters, save/load/migration/corruption, Blank Core invariants, and emulator liveness.

- [ ] **Step 6: Run full repository verification**

Run unit tests, compileall, shell syntax checks, JSON/schema validation, documentation scans, Git binary checks, and diff-size checks.

- [ ] **Step 7: Update documentation with exact status**

Only executed and observed behavior is marked implemented. Unexecuted optional toolchain or asset paths remain explicit.

- [ ] **Step 8: Commit**

Commit message: `feat: complete functional Task 8 Custom Blader foundation`.

---

## Acceptance Gate

The milestone is ready to merge only when all of these are true:

- New Game enters the creator and existing saves bypass it.
- The creator completes and cancels without soft lock.
- Player and custom Bey names render in verified native paths.
- At least several evidence-backed avatar/portrait combinations work.
- Palette options do not corrupt shared NPC resources.
- Four origins grant evidence-backed valid starters exactly once.
- Custom identity survives two save/load cycles.
- EEPROM extension use is enabled only after confirmed tail-safety evidence.
- Corrupt newest custom slot falls back to the older valid slot.
- Every interrupted custom write remains recoverable.
- Blank Core remains active through other part changes and cannot be removed.
- Blank Core grants no existing Bit Beast or Special Move.
- Every hook matches exact source bytes and targets a valid allocation.
- BPS application reconstructs the exact output.
- Two clean builds are byte-identical.
- The source ROM SHA-256 remains unchanged.
- No ROM, BPS, save, state, dump, screenshot, generated binary, or commercial asset is tracked.
- All tests pass and runtime evidence is recorded honestly.

## Post-Task-8 Milestone Sequence

After this PR merges, continue autonomously with separate plans and PRs in this order:

1. Metal Saga category and component conversion.
2. Type identity and battle-resource prototype.
3. Graphics and asset conversion pipeline.
4. Bey Spirit, affinity, Bond, and Resonance foundation.
5. Part/Spirit/Signature Move framework.
6. Launch overhaul and stadium positioning.
7. Battle AI and adaptive rival systems.
8. Original campaign and Metal Fusion cast integration.
9. Presentation, effects, audio, and content completion.
10. Balance, migration, regression, and release QA.
