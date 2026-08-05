import hashlib
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.build.hooks import thumb_bl
from tools.build.modules import load_raw
from tools.build.profile import load
from tools.build.toolchain import discover


class Task8NativeBuildTests(unittest.TestCase):
    MODULE_OFFSET = 0x00400000
    HOOK_SITE = 0x000652FA
    ORIGINAL_TARGET = 0x00066390
    MODULE_BYTES = bytes.fromhex("00b566f4c5f900bd")
    MODULE_SHA256 = "2b6b9674e65bffaeb3040740e4aaf5b2cfdf5432d4a02ecda114b780bc37df6e"

    def test_checked_module_has_explained_source_and_exact_bytes(self):
        source = Path("src/native/task8/task8_hooks.S").read_text(encoding="utf-8")
        self.assertIn("Task8_NewGameHook", source)
        self.assertIn("Retail_SelectNewGameDescriptor", source)
        self.assertIn("push {lr}", source)
        self.assertIn("pop {pc}", source)

        module = load_raw(
            "data/build/fixtures/task8-new-game-hook.hex",
            self.MODULE_SHA256,
            encoding="hex",
        )
        self.assertEqual(module["bytes"], self.MODULE_BYTES)
        self.assertEqual(hashlib.sha256(module["bytes"]).hexdigest(), self.MODULE_SHA256)

    def test_module_internal_call_returns_to_retail_descriptor_selector(self):
        # push {lr}; BL from module+2; pop {pc}
        self.assertEqual(
            self.MODULE_BYTES[2:6],
            thumb_bl(self.MODULE_OFFSET + 2, self.ORIGINAL_TARGET),
        )

    def test_hook_branch_targets_module_entry(self):
        self.assertEqual(
            thumb_bl(self.HOOK_SITE, self.MODULE_OFFSET),
            bytes.fromhex("9af381fe"),
        )

    def test_research_profile_installs_only_behavior_preserving_hook(self):
        profile = load("data/build/profiles/task8-research.json")
        self.assertEqual(profile["profile_id"], "task8-research")
        self.assertEqual(len(profile["hooks"]), 1)
        hook = profile["hooks"][0]
        self.assertEqual(hook["site"], "0x000652fa")
        self.assertEqual(hook["expected"], "01f049f8")
        self.assertEqual(hook["destination_allocation"], "task8-new-game-hook")
        self.assertEqual(hook["kind"], "thumb_bl")
        self.assertFalse(profile["smoke_test"]["enabled"])
        self.assertEqual(profile["extension_metadata"]["release_status"], "research-only")

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
        self.assertEqual(provenance["retail_target"], "0x08066390")
        self.assertEqual(provenance["decoded_size"], len(self.MODULE_BYTES))


if __name__ == "__main__":
    unittest.main()
