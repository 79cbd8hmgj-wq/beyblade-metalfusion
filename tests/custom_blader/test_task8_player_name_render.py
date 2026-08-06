import json
import os
import unittest
from pathlib import Path

from src.custom_blader import native_slot
from src.custom_blader.custom_save import serialize_slot
from src.custom_blader.custom_state import default_state
from tools.build.profile import load


class Task8PlayerNameRenderTests(unittest.TestCase):
    def test_python_contract_selects_valid_persistent_name_or_fallback(self):
        state = default_state()
        state.player_name = "Rin-42"
        valid = serialize_slot(state, 3)
        self.assertEqual(native_slot.select_player_name(valid, "Tyson"), "Rin-42")

        corrupt = bytearray(valid)
        corrupt[10] ^= 0x20
        self.assertEqual(native_slot.select_player_name(bytes(corrupt), "Tyson"), "Tyson")
        self.assertEqual(native_slot.select_player_name(bytes(64), "Takao"), "Takao")

    def test_native_profile_declares_guarded_player_name_render_hook(self):
        hooks = Path("src/native/task8/task8_hooks.S").read_text(encoding="utf-8")
        slot = Path("src/native/task8/task8_slot.c").read_text(encoding="utf-8")
        for symbol in (
            "Task8_PlayerNameRenderHook",
            "Task8_SelectPlayerName",
            "Retail_DrawBoundedText",
        ):
            self.assertIn(symbol, hooks + slot)

        profile = load("data/build/profiles/task8-research.json")
        profile_hooks = {item["id"]: item for item in profile["hooks"]}
        hook = profile_hooks["hook-protagonist-name-render"]
        self.assertEqual(hook["site"], "0x0002e5ac")
        self.assertEqual(hook["expected"], "42f092fa")
        self.assertEqual(hook["destination_allocation"], "task8-native-hooks")

        provenance = json.loads(
            Path("data/build/fixtures/task8-new-game-hook.provenance.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertIn("Task8_PlayerNameRenderHook", provenance["entry_symbols"])
        self.assertIn("Task8_SelectPlayerName", provenance["entry_symbols"])
        self.assertEqual(
            provenance["hook_sites"]["player_name_render"]["rom_offset"],
            "0x0002E5AC",
        )
        self.assertEqual(
            provenance["hook_sites"]["player_name_render"]["expected"],
            "42f092fa",
        )
        self.assertEqual(
            provenance["player_name_render"]["fallback_behavior"],
            "preserve retail localized Tyson/Takao pointer when SU8C is invalid",
        )
        self.assertEqual(
            provenance["player_name_render"]["runtime_status"],
            "runtime_confirmed_combined_module",
        )
        evidence = json.loads(
            Path("analysis/task8/player-name-render.json").read_text(encoding="utf-8")
        )
        self.assertEqual(evidence["status"], "runtime_confirmed")
        self.assertEqual(evidence["hook_bytes"], "d1f382fd")
        self.assertEqual(evidence["valid_selection"]["text"], "Rin-42")
        self.assertEqual(
            evidence["invalid_selection"]["selected_pointer"],
            evidence["invalid_selection"]["fallback_pointer"],
        )

    def test_supported_rom_contains_expected_guarded_call_bytes(self):
        rom_path = os.environ.get("BEYBLADE_GREV_ROM")
        if not rom_path:
            self.skipTest("BEYBLADE_GREV_ROM is not set")
        data = Path(rom_path).read_bytes()
        self.assertEqual(data[0x2E5AC:0x2E5B0], bytes.fromhex("42f092fa"))


if __name__ == "__main__":
    unittest.main()
