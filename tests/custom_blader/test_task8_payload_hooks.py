import json
import unittest
from pathlib import Path
from tools.build.profile import load


class Task8PayloadHookTests(unittest.TestCase):
    def test_native_sources_declare_persistence_creator_and_render_contracts(self):
        paths = [Path("src/native/task8/task8_hooks.S"), Path("src/native/task8/task8_slot.c"), Path("src/native/task8/creator.c")]
        source = "\n".join(path.read_text(encoding="utf-8") for path in paths)
        for symbol in (
            "Task8_SavePayloadHook", "Task8_LoadPayloadHook", "Task8_NameCommitHook",
            "Task8_CreatorBackHook", "Task8_PlayerNameRenderHook",
            "Retail_SerializeSavePayload", "Retail_DeserializeSavePayload", "Retail_CopyBytes",
            "Task8_PrepareSlotForSave", "Task8_ValidateOrDefaultSlot", "Task8_CreatorInit",
            "Task8_CreatorCommit", "Task8_CreatorBack", "Task8_SelectPlayerName",
        ):
            self.assertIn(symbol, source)
        self.assertIn("Task8_PayloadSlotFirstOffset, 0x000002F2", source)
        self.assertIn("movs r6, #32", source)
        self.assertIn("adds r4, #12", source)
        self.assertIn("0xEDB88320", source)
        self.assertIn("0x43555354", source)

    def test_profile_installs_six_guarded_hooks_and_runtime_storage(self):
        profile = load("data/build/profiles/task8-research.json")
        allocation = next(item for item in profile["allocations"] if item["id"] == "task8-native-hooks")
        self.assertEqual(allocation["size"], "0x900")
        patch = next(item for item in profile["patches"] if item["id"] == "extend-runtime-root-for-custom-slot")
        self.assertEqual(patch["value"], "0x00001908")
        hooks = {item["id"]: item for item in profile["hooks"]}
        self.assertEqual(set(hooks), {
            "hook-new-game-descriptor-selection", "hook-save-payload-custom-slot",
            "hook-load-payload-custom-slot", "hook-name-entry-custom-slot",
            "hook-name-entry-empty-back", "hook-protagonist-name-render",
        })
        expected = {
            "hook-save-payload-custom-slot":("0x00044e80","00f08af9"),
            "hook-load-payload-custom-slot":("0x00045092","00f07dfa"),
            "hook-name-entry-custom-slot":("0x00066962","0cf059fc"),
            "hook-name-entry-empty-back":("0x000669dc","02202060"),
            "hook-protagonist-name-render":("0x0002e5ac","42f092fa"),
        }
        for key, pair in expected.items():
            self.assertEqual((hooks[key]["site"], hooks[key]["expected"]), pair)

    def test_provenance_exposes_integrity_creator_and_storage(self):
        p = json.loads(Path("data/build/fixtures/task8-new-game-hook.provenance.json").read_text(encoding="utf-8"))
        self.assertEqual(p["payload_storage"]["record_stride"], "0x0C")
        self.assertEqual(p["payload_storage"]["records_used"], 32)
        self.assertTrue(p["slot_integrity"]["crc32_enabled"])
        self.assertTrue(p["creator"]["retail_keyboard_reused"])
        self.assertTrue(p["player_name_render"]["localized_fallback_preserved"])


if __name__ == "__main__":
    unittest.main()
