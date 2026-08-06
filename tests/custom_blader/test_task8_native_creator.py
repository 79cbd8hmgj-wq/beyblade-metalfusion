import json
import unittest
from pathlib import Path

from tools.build.profile import load


class Task8NativeCreatorTests(unittest.TestCase):
    def test_native_creator_declares_staged_retail_scene_contract(self):
        hooks = Path("src/native/task8/task8_hooks.S").read_text(encoding="utf-8")
        creator_path = Path("src/native/task8/creator.c")
        header_path = Path("src/native/task8/creator.h")
        self.assertTrue(creator_path.is_file(), "implement native creator")
        self.assertTrue(header_path.is_file(), "declare native creator ABI")
        creator = creator_path.read_text(encoding="utf-8")
        header = header_path.read_text(encoding="utf-8")

        for symbol in (
            "Task8_CreatorInit",
            "Task8_CreatorCommit",
            "Task8_CreatorBack",
            "Task8_CreatorRefresh",
            "Task8_CreatorBackHook",
            "Task8_CallRetailSetText",
            "Task8_CallRetailUpdateNameCursor",
        ):
            self.assertIn(symbol, hooks + creator + header)

        for prompt in (
            "Blader name",
            "Bey name",
            "Avatar 1-4",
            "Skin 1-4",
            "Hair 1-4",
            "Outfit 1-4",
            "Portrait 1-4",
            "Origin 1-4",
            "Style 1-4",
            "Confirm Y/N",
        ):
            self.assertIn(prompt, creator)

        for contract in (
            "TASK8_CREATOR_STAGE_PLAYER_NAME",
            "TASK8_CREATOR_STAGE_BEY_NAME",
            "TASK8_CREATOR_STAGE_AVATAR",
            "TASK8_CREATOR_STAGE_SKIN",
            "TASK8_CREATOR_STAGE_HAIR",
            "TASK8_CREATOR_STAGE_OUTFIT",
            "TASK8_CREATOR_STAGE_PORTRAIT",
            "TASK8_CREATOR_STAGE_ORIGIN",
            "TASK8_CREATOR_STAGE_TENDENCY",
            "TASK8_CREATOR_STAGE_CONFIRM",
            "TASK8_CREATOR_COMPLETE",
        ):
            self.assertIn(contract, header)

    def test_profile_installs_name_commit_and_empty_back_hooks(self):
        profile = load("data/build/profiles/task8-research.json")
        hooks = {item["id"]: item for item in profile["hooks"]}
        self.assertIn("hook-name-entry-custom-slot", hooks)
        self.assertIn("hook-name-entry-empty-back", hooks)

        name_hook = hooks["hook-name-entry-custom-slot"]
        self.assertEqual(name_hook["site"], "0x00066962")
        self.assertEqual(name_hook["expected"], "0cf059fc")

        back_hook = hooks["hook-name-entry-empty-back"]
        self.assertEqual(back_hook["site"], "0x000669dc")
        self.assertEqual(back_hook["expected"], "02202060")
        self.assertEqual(
            back_hook["destination_allocation"],
            "task8-native-hooks",
        )

    def test_provenance_exposes_creator_entries_and_retail_primitives(self):
        provenance = json.loads(
            Path(
                "data/build/fixtures/task8-new-game-hook.provenance.json"
            ).read_text(encoding="utf-8")
        )
        entries = provenance["entry_symbols"]
        for symbol in (
            "Task8_CreatorInit",
            "Task8_CreatorCommit",
            "Task8_CreatorBack",
            "Task8_CreatorRefresh",
            "Task8_CreatorBackHook",
        ):
            self.assertIn(symbol, entries)

        retail = provenance["retail_symbols"]
        self.assertEqual(retail["Retail_SetText"], "0x08070AD5")
        self.assertEqual(retail["Retail_UpdateNameCursor"], "0x08066AD5")
        self.assertEqual(
            provenance["hook_sites"]["creator_back"]["rom_offset"],
            "0x000669DC",
        )
        self.assertTrue(provenance["creator"]["retail_keyboard_reused"])
        self.assertTrue(provenance["creator"]["backtracking_enabled"])
        self.assertEqual(provenance["creator"]["selection_count"], 7)
        self.assertEqual(provenance["creator"]["option_range"], [1, 4])
        self.assertFalse(provenance["creator"]["existing_save_entry"])


if __name__ == "__main__":
    unittest.main()
