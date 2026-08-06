import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.build.bps import apply as apply_bps
from tools.build.build_rom import build
from tools.build.hooks import thumb_bl
from tools.build.modules import load_raw
from tools.build.profile import load
from tools.build.toolchain import discover


PROVENANCE_PATH = Path(
    "data/build/fixtures/task8-new-game-hook.provenance.json"
)
MODULE_PATH = Path("data/build/fixtures/task8-new-game-hook.hex")
PROVENANCE = json.loads(PROVENANCE_PATH.read_text(encoding="utf-8"))
MODULE_BYTES = bytes.fromhex(MODULE_PATH.read_text(encoding="utf-8").strip())
MODULE_SHA256 = PROVENANCE["decoded_sha256"]
ENTRY_OFFSETS = {
    name: int(value, 0)
    for name, value in PROVENANCE["entry_symbols"].items()
}


class Task8NativeBuildTests(unittest.TestCase):
    MODULE_OFFSET = 0x00400000
    HOOK_ENTRY_SYMBOLS = {
        "hook-new-game-descriptor-selection": "Task8_NewGameHook",
        "hook-save-payload-custom-slot": "Task8_SavePayloadHook",
        "hook-load-payload-custom-slot": "Task8_LoadPayloadHook",
        "hook-name-entry-custom-slot": "Task8_NameCommitHook",
        "hook-name-entry-empty-back": "Task8_CreatorBackHook",
    }

    @staticmethod
    def changed_offsets_for_replacement(offset, before, after):
        if len(before) != len(after):
            raise ValueError("replacement extents differ")
        return [
            offset + index
            for index, pair in enumerate(zip(before, after))
            if pair[0] != pair[1]
        ]

    def test_checked_module_has_explained_source_and_exact_bytes(self):
        sources = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (
                Path("src/native/task8/task8_hooks.S"),
                Path("src/native/task8/creator.c"),
                Path("src/native/task8/creator.h"),
                Path("src/native/task8/task8_slot.c"),
            )
        )
        for symbol in PROVENANCE["entry_symbols"]:
            self.assertIn(symbol, sources)
        for symbol in (
            "Task8_CallSelectNewGameDescriptor",
            "Task8_CallSerializeSavePayload",
            "Task8_CallDeserializeSavePayload",
            "Task8_CallRetailCopyBytes",
            "Task8_CallRetailSetText",
            "Task8_CallRetailUpdateNameCursor",
        ):
            self.assertIn(symbol, sources)

        module = load_raw(
            MODULE_PATH,
            MODULE_SHA256,
            encoding="hex",
        )
        self.assertEqual(module["bytes"], MODULE_BYTES)
        self.assertEqual(
            hashlib.sha256(module["bytes"]).hexdigest(),
            MODULE_SHA256,
        )
        self.assertEqual(len(module["bytes"]), PROVENANCE["decoded_size"])

        profile = load("data/build/profiles/task8-research.json")
        allocation = next(
            item
            for item in profile["allocations"]
            if item["id"] == "task8-native-hooks"
        )
        self.assertLessEqual(len(MODULE_BYTES), int(allocation["size"], 0))
        self.assertEqual(
            PROVENANCE["allocation_size"],
            allocation["size"],
        )

    def test_entry_section_keeps_guarded_hooks_at_stable_offsets(self):
        expected = {
            "Task8_NewGameHook": 0x00,
            "Task8_SavePayloadHook": 0x18,
            "Task8_LoadPayloadHook": 0x48,
            "Task8_NameCommitHook": 0x78,
            "Task8_CreatorBackHook": 0x98,
        }
        for symbol, offset in expected.items():
            self.assertEqual(ENTRY_OFFSETS[symbol], offset)
        self.assertEqual(ENTRY_OFFSETS["Task8_CreatorInit"], 0xF4)
        self.assertEqual(ENTRY_OFFSETS["Task8_PromptBladerNameRow"], 0x754)

        linker = Path("tools/build/linker.py").read_text(encoding="utf-8")
        hooks = Path("src/native/task8/task8_hooks.S").read_text(
            encoding="utf-8"
        )
        self.assertIn("*(.text.task8_entry) *(.text*)", linker)
        self.assertIn('.section .text.task8_entry,"ax",%progbits', hooks)
        self.assertIn("*(.ARM.exidx*)", linker)
        self.assertIn("*(.ARM.extab*)", linker)

    def test_retail_literals_and_creator_prompt_row_are_present(self):
        literal_values = {
            int.from_bytes(MODULE_BYTES[offset : offset + 4], "little")
            for offset in range(0, len(MODULE_BYTES) - 3, 4)
        }
        for address in (
            0x03000198,
            0x030009AC,
            0x08066391,
            0x08045199,
            0x08045591,
            0x08073219,
            0x08070AD5,
            0x08066AD5,
        ):
            self.assertIn(address, literal_values)

        row_offset = ENTRY_OFFSETS["Task8_PromptBladerNameRow"]
        prompt_pointer = int.from_bytes(
            MODULE_BYTES[row_offset : row_offset + 4],
            "little",
        )
        self.assertEqual(prompt_pointer, 0x08400748)
        self.assertEqual(
            MODULE_BYTES[row_offset : row_offset + 20],
            prompt_pointer.to_bytes(4, "little") * 5,
        )

    def test_guarded_hook_branches_target_module_entries(self):
        profile = load("data/build/profiles/task8-research.json")
        hooks = {item["id"]: item for item in profile["hooks"]}
        self.assertEqual(set(hooks), set(self.HOOK_ENTRY_SYMBOLS))

        expected_patch_bytes = {
            "hook-new-game-descriptor-selection": "9af381fe",
            "hook-save-payload-custom-slot": "bbf3caf8",
            "hook-load-payload-custom-slot": "baf3d9ff",
            "hook-name-entry-custom-slot": "99f389fb",
            "hook-name-entry-empty-back": "99f35cfb",
        }
        for hook_id, entry_symbol in self.HOOK_ENTRY_SYMBOLS.items():
            hook = hooks[hook_id]
            site = int(hook["site"], 0)
            destination_offset = int(hook["destination_offset"], 0)
            self.assertEqual(destination_offset, ENTRY_OFFSETS[entry_symbol])
            self.assertEqual(
                thumb_bl(site, self.MODULE_OFFSET + destination_offset),
                bytes.fromhex(expected_patch_bytes[hook_id]),
            )

    def test_research_profile_installs_creator_and_persistence_changes(self):
        profile = load("data/build/profiles/task8-research.json")
        self.assertEqual(profile["profile_id"], "task8-research")
        self.assertEqual(len(profile["hooks"]), 5)
        patches = {item["id"]: item for item in profile["patches"]}
        self.assertEqual(
            set(patches),
            {
                "extend-runtime-root-for-custom-slot",
                "replace-name-entry-prompt-row",
            },
        )
        self.assertEqual(
            patches["extend-runtime-root-for-custom-slot"]["value"],
            "0x00001908",
        )
        prompt_patch = patches["replace-name-entry-prompt-row"]
        self.assertEqual(prompt_patch["offset"], "0x000bae68")
        self.assertEqual(prompt_patch["expected"], "006d0908")
        self.assertEqual(prompt_patch["value"], "0x08400754")

        metadata = profile["extension_metadata"]
        self.assertEqual(metadata["release_status"], "research-only")
        self.assertTrue(metadata["creator_enabled"])
        self.assertTrue(metadata["retail_name_capture_enabled"])
        self.assertFalse(metadata["creator_existing_save_entry"])
        self.assertFalse(metadata["native_eeprom_tail_enabled"])

    def test_toolchain_discovery_prefers_gnu_then_llvm(self):
        gnu = {
            "arm-none-eabi-gcc": "/gnu/gcc",
            "arm-none-eabi-as": "/gnu/as",
            "arm-none-eabi-ld": "/gnu/ld",
            "arm-none-eabi-objcopy": "/gnu/objcopy",
        }
        llvm = {
            "clang": "/llvm/clang",
            "ld.lld": "/llvm/ld.lld",
            "llvm-objcopy": "/llvm/llvm-objcopy",
        }

        with patch(
            "tools.build.toolchain.shutil.which",
            side_effect=lambda name: gnu.get(name) or llvm.get(name),
        ):
            info = discover()
        self.assertTrue(info["available"])
        self.assertEqual(info["provider"], "gnu-arm-none-eabi")

        with patch(
            "tools.build.toolchain.shutil.which",
            side_effect=lambda name: llvm.get(name),
        ):
            info = discover()
        self.assertTrue(info["available"])
        self.assertEqual(info["provider"], "llvm-arm-none-eabi")
        self.assertEqual(
            set(info["tools"]),
            {"clang", "ld.lld", "llvm-objcopy"},
        )

        with patch("tools.build.toolchain.shutil.which", return_value=None):
            info = discover()
        self.assertFalse(info["available"])
        self.assertIsNone(info["provider"])

    def test_module_provenance_matches_checked_hex(self):
        self.assertEqual(PROVENANCE["decoded_sha256"], MODULE_SHA256)
        self.assertEqual(PROVENANCE["load_address"], "0x08400000")
        self.assertEqual(PROVENANCE["entry_symbol"], "Task8_NewGameHook")
        self.assertEqual(PROVENANCE["decoded_size"], len(MODULE_BYTES))
        self.assertTrue(
            PROVENANCE["local_verification"]["source_and_checked_hex_equal"]
        )
        self.assertTrue(
            PROVENANCE["local_verification"]["host_creator_state_machine"]
            == "passed"
        )
        self.assertTrue(PROVENANCE["slot_integrity"]["crc32_enabled"])
        self.assertTrue(PROVENANCE["creator"]["backtracking_enabled"])
        self.assertTrue(PROVENANCE["name_commit"]["retail_copy_preserved"])

    def test_real_research_profile_when_rom_is_supplied(self):
        rom_value = os.environ.get("BEYBLADE_GREV_ROM")
        if not rom_value:
            self.skipTest("BEYBLADE_GREV_ROM is not set")
        rom = Path(rom_value)
        if not rom.is_file():
            self.skipTest("BEYBLADE_GREV_ROM does not point to a file")
        source_before = rom.read_bytes()
        self.assertEqual(
            hashlib.sha256(source_before).hexdigest(),
            "c4a568adc896bace0e25dbff4aa0c1802933c88e3f4a4e825075116c8c4173e5",
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output_a = root / "a"
            output_b = root / "b"
            manifest_a = build(
                rom,
                "data/build/profiles/task8-research.json",
                output_a,
                clean=True,
            )
            manifest_b = build(
                rom,
                "data/build/profiles/task8-research.json",
                output_b,
                clean=True,
            )
            deterministic_files = [
                "spirit-unbound-task8-research.gba",
                "spirit-unbound-task8-research.bps",
                "build-manifest.json",
                "allocation-map.json",
                "allocation-map.csv",
                "changed-ranges.json",
                "hooks.json",
                "modules.json",
                "validation.json",
                "build-report.md",
            ]
            for name in deterministic_files:
                self.assertEqual(
                    (output_a / name).read_bytes(),
                    (output_b / name).read_bytes(),
                    name,
                )
            built = (
                output_a / "spirit-unbound-task8-research.gba"
            ).read_bytes()
            patch_bytes = (
                output_a / "spirit-unbound-task8-research.bps"
            ).read_bytes()
            self.assertEqual(len(built), 0x00800000)

            profile = load("data/build/profiles/task8-research.json")
            replacements = []
            for hook in profile["hooks"]:
                site = int(hook["site"], 0)
                destination = self.MODULE_OFFSET + int(
                    hook["destination_offset"], 0
                )
                replacements.append(
                    (
                        site,
                        bytes.fromhex(hook["expected"]),
                        thumb_bl(site, destination),
                    )
                )
            for profile_patch in profile["patches"]:
                self.assertEqual(profile_patch["kind"], "write_u32")
                replacements.append(
                    (
                        int(profile_patch["offset"], 0),
                        bytes.fromhex(profile_patch["expected"]),
                        int(profile_patch["value"], 0).to_bytes(4, "little"),
                    )
                )

            expected_changed_offsets = []
            for offset, original, replacement in replacements:
                self.assertEqual(
                    built[offset : offset + len(replacement)],
                    replacement,
                )
                expected_changed_offsets.extend(
                    self.changed_offsets_for_replacement(
                        offset,
                        original,
                        replacement,
                    )
                )
            expected_changed_offsets.sort()

            self.assertEqual(
                built[
                    self.MODULE_OFFSET : self.MODULE_OFFSET
                    + len(MODULE_BYTES)
                ],
                MODULE_BYTES,
            )
            actual_changed_offsets = [
                index
                for index, pair in enumerate(zip(source_before, built))
                if pair[0] != pair[1]
            ]
            self.assertEqual(actual_changed_offsets, expected_changed_offsets)
            self.assertEqual(apply_bps(patch_bytes, source_before), built)
            self.assertEqual(
                manifest_a["build_id"],
                manifest_b["build_id"],
            )
            self.assertEqual(
                manifest_a["output_sha256"],
                manifest_b["output_sha256"],
            )
        self.assertEqual(rom.read_bytes(), source_before)


if __name__ == "__main__":
    unittest.main()
