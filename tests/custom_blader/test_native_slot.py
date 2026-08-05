import importlib
import importlib.util
import unittest

from src.custom_blader.custom_save import parse_slot, serialize_slot
from src.custom_blader.custom_state import CustomBladerState, default_state, sanitize


MODULE_NAME = "src.custom_blader.native_slot"


class NativeSlotTests(unittest.TestCase):
    def module(self):
        if importlib.util.find_spec(MODULE_NAME) is None:
            self.skipTest("native_slot production module is not implemented yet")
        return importlib.import_module(MODULE_NAME)

    def test_native_slot_module_exists(self):
        self.assertIsNotNone(
            importlib.util.find_spec(MODULE_NAME),
            "implement src.custom_blader.native_slot",
        )

    def test_default_slot_matches_canonical_serializer(self):
        native_slot = self.module()
        self.assertEqual(
            native_slot.default_slot(),
            serialize_slot(default_state(), 0),
        )
        self.assertTrue(native_slot.validate_slot(native_slot.default_slot()))

    def test_validation_matches_current_slot_parser_for_valid_states(self):
        native_slot = self.module()
        states = [
            default_state(),
            sanitize(
                CustomBladerState(
                    initialized=1,
                    player_name="Nova",
                    bey_name="Astra",
                    avatar_id=2,
                    portrait_id=3,
                    skin_palette_id=1,
                    hair_style_id=2,
                    hair_palette_id=3,
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
            ),
        ]
        for sequence, state in enumerate(states, start=3):
            raw = serialize_slot(state, sequence)
            parsed = parse_slot(raw)
            self.assertTrue(parsed[0], parsed[3])
            self.assertTrue(native_slot.validate_slot(raw))
            self.assertEqual(native_slot.state_validation(raw), state.validation)

    def test_validation_rejects_every_integrity_layer(self):
        native_slot = self.module()
        valid = bytearray(native_slot.default_slot())
        corruptions = {
            "magic": (0, valid[0] ^ 1),
            "schema": (8, 2),
            "player-id": (34, 4),
            "hair-avatar-mismatch": (37, 1),
            "blank-core-state": (42, 1),
            "blank-core-id": (43, 1),
            "state-validation": (50, valid[50] ^ 1),
            "reserved": (54, 1),
            "crc": (56, valid[56] ^ 1),
            "commit": (60, valid[60] ^ 1),
        }
        for label, (offset, value) in corruptions.items():
            raw = bytearray(valid)
            raw[offset] = value
            self.assertFalse(native_slot.validate_slot(bytes(raw)), label)

    def test_seal_slot_recomputes_state_validation_crc_and_commit(self):
        native_slot = self.module()
        raw = bytearray(native_slot.default_slot())
        raw[4:8] = (19).to_bytes(4, "little")
        raw[10:22] = b"Rin\0" + bytes(8)
        raw[22:34] = b"Comet\0" + bytes(6)
        raw[34] = 3
        raw[37] = 3
        raw[40] = 2
        raw[41] = 1
        raw[44] = 37
        raw[45] = 0x80
        raw[46:50] = bytes([22, 7, 4, 11])
        raw[50:64] = bytes(14)

        sealed = native_slot.seal_slot(bytes(raw))

        self.assertEqual(sealed[4:8], (19).to_bytes(4, "little"))
        self.assertEqual(sealed[54:56], b"\0\0")
        self.assertEqual(sealed[60:64], b"OK8!")
        self.assertTrue(native_slot.validate_slot(sealed))
        valid, sequence, state, status = parse_slot(sealed)
        self.assertTrue(valid, status)
        self.assertEqual(sequence, 19)
        self.assertEqual(state.player_name, "Rin")
        self.assertEqual(state.bey_name, "Comet")
        self.assertEqual(state.avatar_id, 3)
        self.assertEqual(state.hair_style_id, 3)
        self.assertEqual(state.current_template_id, 37)
        self.assertEqual(state.future_flags, 0x80)
        self.assertEqual(
            (state.attack_ring_id, state.weight_disk_id, state.spin_gear_id, state.blade_base_id),
            (22, 7, 4, 11),
        )

    def test_initialize_default_replaces_corrupt_slot_deterministically(self):
        native_slot = self.module()
        corrupt = bytearray(native_slot.default_slot())
        corrupt[0] ^= 0xFF
        initialized, status = native_slot.validate_or_default(bytes(corrupt))
        self.assertEqual(status, "defaulted")
        self.assertEqual(initialized, native_slot.default_slot())

        valid = serialize_slot(default_state(), 9)
        preserved, status = native_slot.validate_or_default(valid)
        self.assertEqual(status, "valid")
        self.assertEqual(preserved, valid)

    def test_slot_length_is_strict(self):
        native_slot = self.module()
        for raw in (b"", bytes(63), bytes(65)):
            self.assertFalse(native_slot.validate_slot(raw))
            with self.assertRaisesRegex(ValueError, "64 bytes"):
                native_slot.seal_slot(raw)
            with self.assertRaisesRegex(ValueError, "64 bytes"):
                native_slot.state_validation(raw)


if __name__ == "__main__":
    unittest.main()
