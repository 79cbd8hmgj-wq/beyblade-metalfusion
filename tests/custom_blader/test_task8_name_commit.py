import json
import unittest
from pathlib import Path

from src.custom_blader.custom_save import parse_slot, serialize_slot
from src.custom_blader.custom_state import CustomBladerState, sanitize
from src.custom_blader import native_slot
from tools.build.profile import load


class Task8NameCommitTests(unittest.TestCase):
    def configured_slot(self):
        state = sanitize(
            CustomBladerState(
                initialized=1,
                player_name="Before",
                bey_name="Comet",
                avatar_id=2,
                portrait_id=2,
                skin_palette_id=3,
                hair_style_id=2,
                hair_palette_id=1,
                outfit_palette_id=2,
                origin_id=1,
                tendency_id=3,
                current_template_id=17,
                attack_ring_id=12,
                weight_disk_id=9,
                spin_gear_id=5,
                blade_base_id=21,
                future_flags=0x44,
            )
        )
        return serialize_slot(state, 9)

    def test_python_model_commits_retail_name_and_preserves_other_state(self):
        raw = self.configured_slot()
        retail_buffer = b"ABCDEFGHIJKLMNO\0"
        committed, status = native_slot.commit_player_name(raw, retail_buffer)
        self.assertEqual(status, "committed")
        self.assertTrue(native_slot.validate_slot(committed))

        valid, sequence, state, message = parse_slot(committed)
        self.assertTrue(valid, message)
        self.assertEqual(sequence, 9)
        self.assertEqual(state.player_name, "ABCDEFGHIJKL")
        self.assertEqual(state.bey_name, "Comet")
        self.assertEqual(state.avatar_id, 2)
        self.assertEqual(state.portrait_id, 2)
        self.assertEqual(state.origin_id, 1)
        self.assertEqual(state.tendency_id, 3)
        self.assertEqual(state.current_template_id, 17)
        self.assertEqual(
            (
                state.attack_ring_id,
                state.weight_disk_id,
                state.spin_gear_id,
                state.blade_base_id,
            ),
            (12, 9, 5, 21),
        )

    def test_python_model_handles_short_invalid_and_wrong_size_buffers(self):
        raw = self.configured_slot()
        short_name = b"Nova\0" + bytes(11)
        committed, status = native_slot.commit_player_name(raw, short_name)
        self.assertEqual(status, "committed")
        self.assertEqual(parse_slot(committed)[2].player_name, "Nova")

        invalid_name = b"Bad!\0" + bytes(11)
        defaulted, status = native_slot.commit_player_name(raw, invalid_name)
        self.assertEqual(status, "defaulted")
        self.assertEqual(defaulted, native_slot.default_slot())

        for buffer in (b"", bytes(15), bytes(17)):
            with self.assertRaisesRegex(ValueError, "16 bytes"):
                native_slot.commit_player_name(raw, buffer)

    def test_native_module_and_profile_declare_guarded_name_commit_hook(self):
        hooks = Path("src/native/task8/task8_hooks.S").read_text(encoding="utf-8")
        slot = Path("src/native/task8/task8_slot.c").read_text(encoding="utf-8")
        for symbol in (
            "Task8_NameCommitHook",
            "Task8_CommitPlayerName",
            "Retail_CopyBytes",
        ):
            self.assertIn(symbol, hooks + slot)

        profile = load("data/build/profiles/task8-research.json")
        profile_hooks = {item["id"]: item for item in profile["hooks"]}
        self.assertIn("hook-name-entry-custom-slot", profile_hooks)
        hook = profile_hooks["hook-name-entry-custom-slot"]
        self.assertEqual(hook["site"], "0x00066962")
        self.assertEqual(hook["expected"], "0cf059fc")
        self.assertEqual(hook["destination_allocation"], "task8-native-hooks")

        provenance = json.loads(
            Path(
                "data/build/fixtures/task8-new-game-hook.provenance.json"
            ).read_text(encoding="utf-8")
        )
        self.assertIn("Task8_NameCommitHook", provenance["entry_symbols"])
        self.assertIn("Task8_CommitPlayerName", provenance["entry_symbols"])
        self.assertEqual(
            provenance["hook_sites"]["name_commit"]["rom_offset"],
            "0x00066962",
        )
        self.assertEqual(
            provenance["hook_sites"]["name_commit"]["expected"],
            "0cf059fc",
        )
        self.assertTrue(
            provenance["name_commit"]["retail_copy_preserved"]
        )
        self.assertEqual(
            provenance["name_commit"]["persistent_name_bytes"],
            12,
        )
        self.assertTrue(
            provenance["runtime_verification"]["current_integrity_module"].startswith(
                "confirmed"
            )
        )
        self.assertTrue(
            provenance["runtime_verification"]["name_commit_hook"].startswith(
                "confirmed"
            )
        )

        name_evidence = json.loads(
            Path("analysis/task8/name-entry.json").read_text(encoding="utf-8")
        )["native_persistence"]
        self.assertEqual(name_evidence["status"], "runtime_confirmed")
        self.assertEqual(name_evidence["runtime_evidence"]["hook_bytes"], "99f389fb")
        self.assertEqual(name_evidence["runtime_evidence"]["valid_name"], "Rin-42")
        self.assertTrue(name_evidence["runtime_evidence"]["invalid_name_defaulted"])


if __name__ == "__main__":
    unittest.main()
