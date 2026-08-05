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


class Task8NativeBuildTests(unittest.TestCase):
    MODULE_OFFSET = 0x00400000
    NEW_GAME_HOOK_SITE = 0x000652FA
    SAVE_HOOK_SITE = 0x00044E80
    LOAD_HOOK_SITE = 0x00045092
    ROOT_SIZE_SITE = 0x0004612C
    ORIGINAL_NEW_GAME_TARGET = 0x00066390
    MODULE_BYTES = bytes.fromhex(
        "00b500f029f800bdf0b5041c00f026f8144d2d6814482d181448241820262878"
        "20706878607002350c34013ef7d1f0bdf0b5041c00f014f80a4d2d680a482d18"
        "0a482418202620782870607868700c340235013ef7d1f0bd054b1847054b1847"
        "054b184798010003c8180000f2020000916306089951040891550408"
    )
    MODULE_SHA256 = "78b18bad83aa49bca3f61f7efa5c829b4bd070177411ddbdb3c19b01ae11120d"

    def test_checked_module_has_explained_source_and_exact_bytes(self):
        source = Path("src/native/task8/task8_hooks.S").read_text(encoding="utf-8")
        for symbol in (
            "Task8_NewGameHook",
            "Task8_SavePayloadHook",
            "Task8_LoadPayloadHook",
            "Task8_CallSelectNewGameDescriptor",
            "Task8_CallSerializeSavePayload",
            "Task8_CallDeserializeSavePayload",
        ):
            self.assertIn(symbol, source)
        self.assertIn("push {lr}", source)
        self.assertIn("push {r4-r7, lr}", source)
        self.assertIn("pop {r4-r7, pc}", source)

        module = load_raw(
            "data/build/fixtures/task8-new-game-hook.hex",
            self.MODULE_SHA256,
            encoding="hex",
        )
        self.assertEqual(module["bytes"], self.MODULE_BYTES)
        self.assertEqual(hashlib.sha256(module["bytes"]).hexdigest(), self.MODULE_SHA256)
        self.assertEqual(len(module["bytes"]), 0x7C)

    def test_module_internal_new_game_call_returns_to_retail_selector(self):
        # push {lr}; BL from module+2 to the local veneer at module+0x58.
        self.assertEqual(
            self.MODULE_BYTES[2:6],
            thumb_bl(self.MODULE_OFFSET + 2, self.MODULE_OFFSET + 0x58),
        )
        self.assertEqual(
            int.from_bytes(self.MODULE_BYTES[0x70:0x74], "little"),
            0x08066391,
        )

    def test_guarded_hook_branches_target_module_entries(self):
        self.assertEqual(
            thumb_bl(self.NEW_GAME_HOOK_SITE, self.MODULE_OFFSET),
            bytes.fromhex("9af381fe"),
        )
        self.assertEqual(
            thumb_bl(self.SAVE_HOOK_SITE, self.MODULE_OFFSET + 0x08),
            bytes.fromhex("bbf3c2f8"),
        )
        self.assertEqual(
            thumb_bl(self.LOAD_HOOK_SITE, self.MODULE_OFFSET + 0x30),
            bytes.fromhex("baf3cdff"),
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
        for hook in hooks.values():
            self.assertEqual(hook["destination_allocation"], "task8-native-hooks")
            self.assertEqual(hook["kind"], "thumb_bl")
        root_patch = profile["patches"][0]
        self.assertEqual(root_patch["offset"], "0x0004612c")
        self.assertEqual(root_patch["expected"], "c8180000")
        self.assertEqual(root_patch["value"], "0x00001908")
        self.assertFalse(profile["smoke_test"]["enabled"])
        self.assertEqual(profile["extension_metadata"]["release_status"], "research-only")
        self.assertFalse(profile["extension_metadata"]["native_eeprom_tail_enabled"])

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

        with patch("tools.build.toolchain.shutil.which", side_effect=lambda name: gnu.get(name) or llvm.get(name)):
            info = discover()
        self.assertTrue(info["available"])
        self.assertEqual(info["provider"], "gnu-arm-none-eabi")

        with patch("tools.build.toolchain.shutil.which", side_effect=lambda name: llvm.get(name)):
            info = discover()
        self.assertTrue(info["available"])
        self.assertEqual(info["provider"], "llvm-arm-none-eabi")
        self.assertEqual(set(info["tools"]), {"clang", "ld.lld", "llvm-objcopy"})

        with patch("tools.build.toolchain.shutil.which", return_value=None):
            info = discover()
        self.assertFalse(info["available"])
        self.assertIsNone(info["provider"])

    def test_module_provenance_matches_checked_hex(self):
        provenance = json.loads(
            Path("data/build/fixtures/task8-new-game-hook.provenance.json").read_text(encoding="utf-8")
        )
        self.assertEqual(provenance["decoded_sha256"], self.MODULE_SHA256)
        self.assertEqual(provenance["load_address"], "0x08400000")
        self.assertEqual(provenance["entry_symbol"], "Task8_NewGameHook")
        self.assertEqual(provenance["entry_symbols"]["Task8_SavePayloadHook"], "0x00000008")
        self.assertEqual(provenance["entry_symbols"]["Task8_LoadPayloadHook"], "0x00000030")
        self.assertEqual(provenance["decoded_size"], len(self.MODULE_BYTES))
        self.assertTrue(provenance["local_verification"]["source_and_checked_hex_equal"])

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
                self.assertEqual((output_a / name).read_bytes(), (output_b / name).read_bytes(), name)
            built = (output_a / "spirit-unbound-task8-research.gba").read_bytes()
            patch_bytes = (output_a / "spirit-unbound-task8-research.bps").read_bytes()
            self.assertEqual(len(built), 0x00800000)
            self.assertEqual(
                built[self.NEW_GAME_HOOK_SITE:self.NEW_GAME_HOOK_SITE + 4],
                bytes.fromhex("9af381fe"),
            )
            self.assertEqual(
                built[self.SAVE_HOOK_SITE:self.SAVE_HOOK_SITE + 4],
                bytes.fromhex("bbf3c2f8"),
            )
            self.assertEqual(
                built[self.LOAD_HOOK_SITE:self.LOAD_HOOK_SITE + 4],
                bytes.fromhex("baf3cdff"),
            )
            self.assertEqual(
                built[self.ROOT_SIZE_SITE:self.ROOT_SIZE_SITE + 4],
                bytes.fromhex("08190000"),
            )
            self.assertEqual(
                built[self.MODULE_OFFSET:self.MODULE_OFFSET + len(self.MODULE_BYTES)],
                self.MODULE_BYTES,
            )
            expected_changed_offsets = [
                *range(self.SAVE_HOOK_SITE, self.SAVE_HOOK_SITE + 4),
                *range(self.LOAD_HOOK_SITE, self.LOAD_HOOK_SITE + 4),
                *range(self.ROOT_SIZE_SITE, self.ROOT_SIZE_SITE + 4),
                *range(self.NEW_GAME_HOOK_SITE, self.NEW_GAME_HOOK_SITE + 4),
            ]
            self.assertEqual(
                [index for index, (before, after) in enumerate(zip(source_before, built)) if before != after],
                expected_changed_offsets,
            )
            self.assertEqual(apply_bps(patch_bytes, source_before), built)
            self.assertEqual(manifest_a["build_id"], manifest_b["build_id"])
            self.assertEqual(manifest_a["output_sha256"], manifest_b["output_sha256"])
        self.assertEqual(rom.read_bytes(), source_before)


if __name__ == "__main__":
    unittest.main()
