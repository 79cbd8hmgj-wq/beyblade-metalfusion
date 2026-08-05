import json
import unittest
from pathlib import Path

from tools.build.profile import load


class Task8PayloadHookTests(unittest.TestCase):
    def test_native_source_declares_save_load_and_runtime_slot_contracts(self):
        source = Path("src/native/task8/task8_hooks.S").read_text(encoding="utf-8")
        for symbol in (
            "Task8_SavePayloadHook",
            "Task8_LoadPayloadHook",
            "Retail_SerializeSavePayload",
            "Retail_DeserializeSavePayload",
            "Task8_RuntimeRootPointer",
            "Task8_CustomSlotOffset",
        ):
            self.assertIn(symbol, source)
        self.assertIn("0x02F2", source)
        self.assertIn("0x0C", source)
        self.assertIn("32", source)

    def test_profile_expands_runtime_root_and_installs_three_guarded_hooks(self):
        profile = load("data/build/profiles/task8-research.json")
        allocation = next(item for item in profile["allocations"] if item["id"] == "task8-native-hooks")
        self.assertGreaterEqual(int(allocation["size"], 0), 0x80)
        self.assertEqual(allocation["fixed_offset"], "0x00400000")

        patch = next(item for item in profile["patches"] if item["id"] == "extend-runtime-root-for-custom-slot")
        self.assertEqual(patch["kind"], "write_u32")
        self.assertEqual(patch["offset"], "0x0004612c")
        self.assertEqual(patch["expected"], "c8180000")
        self.assertEqual(patch["value"], "0x00001908")

        hooks = {item["id"]: item for item in profile["hooks"]}
        self.assertEqual(set(hooks), {
            "hook-new-game-descriptor-selection",
            "hook-save-payload-custom-slot",
            "hook-load-payload-custom-slot",
        })
        self.assertEqual(hooks["hook-save-payload-custom-slot"]["site"], "0x00044e80")
        self.assertEqual(hooks["hook-save-payload-custom-slot"]["expected"], "00f08af9")
        self.assertEqual(hooks["hook-load-payload-custom-slot"]["site"], "0x00045092")
        self.assertEqual(hooks["hook-load-payload-custom-slot"]["expected"], "00f07dfa")
        for hook in hooks.values():
            self.assertEqual(hook["destination_allocation"], "task8-native-hooks")

    def test_module_provenance_exposes_all_entry_offsets_and_runtime_storage(self):
        provenance = json.loads(
            Path("data/build/fixtures/task8-new-game-hook.provenance.json").read_text(encoding="utf-8")
        )
        entries = provenance["entry_symbols"]
        self.assertEqual(set(entries), {
            "Task8_NewGameHook",
            "Task8_SavePayloadHook",
            "Task8_LoadPayloadHook",
        })
        self.assertEqual(entries["Task8_NewGameHook"], "0x00000000")
        self.assertEqual(provenance["runtime_storage"]["root_allocation_old_size"], "0x18C8")
        self.assertEqual(provenance["runtime_storage"]["root_allocation_new_size"], "0x1908")
        self.assertEqual(provenance["runtime_storage"]["custom_slot_offset"], "0x18C8")
        self.assertEqual(provenance["runtime_storage"]["custom_slot_size"], 64)
        self.assertEqual(provenance["payload_storage"]["first_payload_offset"], "0x02F2")
        self.assertEqual(provenance["payload_storage"]["record_stride"], "0x0C")
        self.assertEqual(provenance["payload_storage"]["records_used"], 32)


if __name__ == "__main__":
    unittest.main()
