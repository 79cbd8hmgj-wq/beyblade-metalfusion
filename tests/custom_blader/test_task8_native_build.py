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
    NEW_GAME_HOOK_SITE = 0x000652FA
    SAVE_HOOK_SITE = 0x00044E80
    LOAD_HOOK_SITE = 0x00045092
    ROOT_SIZE_SITE = 0x0004612C

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
        hooks = Path("src/native/task8/task8_hooks.S").read_text(
            encoding="utf-8"
        )
        slot = Path("src/native/task8/task8_slot.c").read_text(
            encoding="utf-8"
        )
        for symbol in (
            "Task8_NewGameHook",
            "Task8_SavePayloadHook",
            "Task8_LoadPayloadHook",
            "Task8_CallSelectNewGameDescriptor",
            "Task8_CallSerializeSavePayload",
            "Task8_CallDeserializeSavePayload",
            "Task8_ValidateSlot",
            "Task8_SealSlot",
            "Task8_InitializeDefaultSlot",
            "Task8_PrepareSlotForSave",
            "Task8_ValidateOrDefaultSlot",
        ):
            self.assertIn(symbol, hooks + slot)
        self.assertIn("push {r4, lr}", hooks)
        self.assertIn("push {r4-r7, lr}", hooks)
        self.assertIn("pop {r4-r7, pc}", hooks)

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
        self.assertLessEqual(len(module["bytes"]), 0x400)

    def test_module_internal_calls_and_retail_veneer_are_stable(self):
        self.assertEqual(
            MODULE_BYTES[0x0C:0x10],
            thumb_bl(
                self.MODULE_OFFSET + 0x0C,
                self.MODULE_OFFSET + ENTRY_OFFSETS["Task8_InitializeDefaultSlot"],
            ),
        )
        self.assertEqual(
            MODULE_BYTES[0x12:0x16],
            thumb_bl(self.MODULE_OFFSET + 0x12, self.MODULE_OFFSET + 0x78),
        )
        self.assertEqual(
            int.from_bytes(MODULE_BYTES[0x90:0x94], "little"),
            0x08066391,
        )

    def test_guarded_hook_branches_target_module_entries(self):
        self.assertEqual(
            thumb_bl(
                self.NEW_GAME_HOOK_SITE,
                self.MODULE_OFFSET + ENTRY_OFFSETS["Task8_NewGameHook"],
            ),
            bytes.fromhex("9af381fe"),
        )
        self.assertEqual(
            thumb_bl(
                self.SAVE_HOOK_SITE,
                self.MODULE_OFFSET + ENTRY_OFFSETS["Task8_SavePayloadHook"],
            ),
            bytes.fromhex("bbf3caf8"),
        )
        self.assertEqual(
            thumb_bl(
                self.LOAD_HOOK_SITE,
                self.MODULE_OFFSET + ENTRY_OFFSETS["Task8_LoadPayloadHook"],
            ),
            bytes.fromhex("baf3d9ff"),
        )

    def test_research_profile_installs_persistence_hooks_and_root_extension(self):
        profile = load("data/build/profiles/task8-research.json")
        self.assertEqual(profile["profile_id"], "task8-research")
        self.assertEqual(len(profile["hooks"]), 3)
        self.assertEqual(len(profile["patches"]), 1)
        hooks = {hook["id"]: hook for hook in profile["hooks"]}
        self.assertEqual(
            hooks["hook-new-game-descriptor-selection"]["site"],
            "0x000652fa",
        )
        self.assertEqual(
            hooks["hook-save-payload-custom-slot"]["site"],
            "0x00044e80",
        )
        self.assertEqual(
            hooks["hook-load-payload-custom-slot"]["site"],
            "0x00045092",
        )
        self.assertEqual(
            int(hooks["hook-save-payload-custom-slot"]["destination_offset"], 0),
            ENTRY_OFFSETS["Task8_SavePayloadHook"],
        )
        self.assertEqual(
            int(hooks["hook-load-payload-custom-slot"]["destination_offset"], 0),
            ENTRY_OFFSETS["Task8_LoadPayloadHook"],
        )
        for hook in hooks.values():
            self.assertEqual(
                hook["destination_allocation"],
                "task8-native-hooks",
            )
            self.assertEqual(hook["kind"], "thumb_bl")
        root_patch = profile["patches"][0]
        self.assertEqual(root_patch["offset"], "0x0004612c")
        self.assertEqual(root_patch["expected"], "c8180000")
        self.assertEqual(root_patch["value"], "0x00001908")
        allocation = next(
            item
            for item in profile["allocations"]
            if item["id"] == "task8-native-hooks"
        )
        self.assertGreaterEqual(int(allocation["size"], 0), len(MODULE_BYTES))
        self.assertFalse(profile["smoke_test"]["enabled"])
        self.assertEqual(
            profile["extension_metadata"]["release_status"],
            "research-only",
        )
        self.assertFalse(
            profile["extension_metadata"]["native_eeprom_tail_enabled"]
        )

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
        self.assertEqual(
            ENTRY_OFFSETS["Task8_SavePayloadHook"],
            0x18,
        )
        self.assertEqual(
            ENTRY_OFFSETS["Task8_LoadPayloadHook"],
            0x48,
        )
        self.assertEqual(PROVENANCE["decoded_size"], len(MODULE_BYTES))
        self.assertTrue(
            PROVENANCE["local_verification"]["source_and_checked_hex_equal"]
        )
        self.assertTrue(PROVENANCE["slot_integrity"]["crc32_enabled"])
        self.assertTrue(
            PROVENANCE["slot_integrity"]["invalid_slot_defaults"]
        )

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
            hook_by_site = {
                int(item["site"], 0): item for item in profile["hooks"]
            }
            replacements = []
            for site, original in (
                (self.SAVE_HOOK_SITE, bytes.fromhex("00f08af9")),
                (self.LOAD_HOOK_SITE, bytes.fromhex("00f07dfa")),
                (self.NEW_GAME_HOOK_SITE, bytes.fromhex("01f049f8")),
            ):
                hook = hook_by_site[site]
                destination = self.MODULE_OFFSET + int(
                    hook["destination_offset"], 0
                )
                replacements.append(
                    (site, original, thumb_bl(site, destination))
                )
            replacements.append(
                (
                    self.ROOT_SIZE_SITE,
                    bytes.fromhex("c8180000"),
                    bytes.fromhex("08190000"),
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
            self.assertEqual(
                actual_changed_offsets,
                expected_changed_offsets,
            )
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
