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

PROVENANCE_PATH = Path("data/build/fixtures/task8-new-game-hook.provenance.json")
MODULE_PATH = Path("data/build/fixtures/task8-new-game-hook.hex")
PROVENANCE = json.loads(PROVENANCE_PATH.read_text(encoding="utf-8"))
MODULE_BYTES = bytes.fromhex(MODULE_PATH.read_text(encoding="utf-8").strip())
ENTRY_OFFSETS = {name: int(value, 0) for name, value in PROVENANCE["entry_symbols"].items()}


class Task8NativeBuildTests(unittest.TestCase):
    MODULE_OFFSET = 0x00400000
    HOOK_ENTRY_SYMBOLS = {
        "hook-new-game-descriptor-selection": "Task8_NewGameHook",
        "hook-save-payload-custom-slot": "Task8_SavePayloadHook",
        "hook-load-payload-custom-slot": "Task8_LoadPayloadHook",
        "hook-name-entry-custom-slot": "Task8_NameCommitHook",
        "hook-name-entry-empty-back": "Task8_CreatorBackHook",
        "hook-protagonist-name-render": "Task8_PlayerNameRenderHook",
    }

    def test_checked_module_matches_provenance_and_all_sources(self):
        sources = [Path(value) for value in PROVENANCE["sources"]]
        self.assertTrue(all(path.is_file() for path in sources))
        source_text = "\n".join(path.read_text(encoding="utf-8") for path in sources)
        for symbol in (
            *self.HOOK_ENTRY_SYMBOLS.values(),
            "Task8_CreatorInit",
            "Task8_CreatorCommit",
            "Task8_CreatorBack",
            "Task8_CreatorRefresh",
            "Task8_ValidateSlot",
            "Task8_SealSlot",
            "Task8_SelectPlayerName",
        ):
            self.assertIn(symbol, source_text)
        module = load_raw(MODULE_PATH, PROVENANCE["decoded_sha256"], encoding="hex")
        self.assertEqual(module["bytes"], MODULE_BYTES)
        self.assertEqual(len(MODULE_BYTES), PROVENANCE["decoded_size"])
        self.assertEqual(hashlib.sha256(MODULE_BYTES).hexdigest(), PROVENANCE["decoded_sha256"])
        profile = load("data/build/profiles/task8-research.json")
        allocation = next(item for item in profile["allocations"] if item["id"] == "task8-native-hooks")
        self.assertLessEqual(len(MODULE_BYTES), int(allocation["size"], 0))
        self.assertEqual(PROVENANCE["allocation_size"], allocation["size"])

    def test_profile_hooks_are_guarded_and_target_provenance_entries(self):
        profile = load("data/build/profiles/task8-research.json")
        hooks = {item["id"]: item for item in profile["hooks"]}
        self.assertEqual(set(hooks), set(self.HOOK_ENTRY_SYMBOLS))
        for hook_id, symbol in self.HOOK_ENTRY_SYMBOLS.items():
            hook = hooks[hook_id]
            self.assertEqual(hook["kind"], "thumb_bl")
            self.assertEqual(hook["destination_allocation"], "task8-native-hooks")
            self.assertEqual(int(hook["destination_offset"], 0), ENTRY_OFFSETS[symbol])
            emitted = thumb_bl(int(hook["site"], 0), self.MODULE_OFFSET + ENTRY_OFFSETS[symbol])
            self.assertEqual(len(emitted), 4)
        prompt_patch = next(item for item in profile["patches"] if item["id"] == "replace-name-entry-prompt-row")
        self.assertEqual(int(prompt_patch["value"], 0), 0x08000000 + self.MODULE_OFFSET + ENTRY_OFFSETS["Task8_PromptBladerNameRow"])

    def test_provenance_exposes_creator_and_render_contracts(self):
        self.assertEqual(ENTRY_OFFSETS["Task8_NewGameHook"], 0)
        self.assertEqual(ENTRY_OFFSETS["Task8_SavePayloadHook"], 0x18)
        self.assertEqual(ENTRY_OFFSETS["Task8_LoadPayloadHook"], 0x48)
        self.assertEqual(ENTRY_OFFSETS["Task8_NameCommitHook"], 0x78)
        self.assertEqual(ENTRY_OFFSETS["Task8_CreatorBackHook"], 0x98)
        self.assertEqual(ENTRY_OFFSETS["Task8_PlayerNameRenderHook"], 0xB4)
        self.assertTrue(PROVENANCE["creator"]["retail_keyboard_reused"])
        self.assertTrue(PROVENANCE["creator"]["backtracking_enabled"])
        self.assertTrue(PROVENANCE["player_name_render"]["localized_fallback_preserved"])
        self.assertEqual(PROVENANCE["retail_symbols"]["Retail_DrawBoundedText"], "0x08070AD5")
        self.assertTrue(PROVENANCE["local_verification"]["source_and_checked_hex_equal"])

    def test_toolchain_discovery_prefers_gnu_then_llvm(self):
        gnu = {"arm-none-eabi-gcc":"/gnu/gcc","arm-none-eabi-as":"/gnu/as","arm-none-eabi-ld":"/gnu/ld","arm-none-eabi-objcopy":"/gnu/objcopy"}
        llvm = {"clang":"/llvm/clang","ld.lld":"/llvm/ld.lld","llvm-objcopy":"/llvm/llvm-objcopy"}
        with patch("tools.build.toolchain.shutil.which", side_effect=lambda name: gnu.get(name) or llvm.get(name)):
            info = discover()
        self.assertEqual(info["provider"], "gnu-arm-none-eabi")
        with patch("tools.build.toolchain.shutil.which", side_effect=lambda name: llvm.get(name)):
            info = discover()
        self.assertEqual(info["provider"], "llvm-arm-none-eabi")
        with patch("tools.build.toolchain.shutil.which", return_value=None):
            self.assertFalse(discover()["available"])

    def test_real_research_profile_is_deterministic_when_rom_is_supplied(self):
        rom_value = os.environ.get("BEYBLADE_GREV_ROM")
        if not rom_value:
            self.skipTest("BEYBLADE_GREV_ROM is not set")
        rom = Path(rom_value)
        source = rom.read_bytes()
        self.assertEqual(hashlib.sha256(source).hexdigest(), "c4a568adc896bace0e25dbff4aa0c1802933c88e3f4a4e825075116c8c4173e5")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); a = root / "a"; b = root / "b"
            ma = build(rom, "data/build/profiles/task8-research.json", a, clean=True)
            mb = build(rom, "data/build/profiles/task8-research.json", b, clean=True)
            for name in ("spirit-unbound-task8-research.gba","spirit-unbound-task8-research.bps","build-manifest.json","allocation-map.json","allocation-map.csv","changed-ranges.json","hooks.json","modules.json","validation.json","build-report.md"):
                self.assertEqual((a/name).read_bytes(), (b/name).read_bytes(), name)
            built = (a/"spirit-unbound-task8-research.gba").read_bytes()
            patch_bytes = (a/"spirit-unbound-task8-research.bps").read_bytes()
            self.assertEqual(apply_bps(patch_bytes, source), built)
            self.assertEqual(ma["build_id"], mb["build_id"])
            self.assertEqual(built[self.MODULE_OFFSET:self.MODULE_OFFSET+len(MODULE_BYTES)], MODULE_BYTES)
        self.assertEqual(rom.read_bytes(), source)


if __name__ == "__main__":
    unittest.main()
