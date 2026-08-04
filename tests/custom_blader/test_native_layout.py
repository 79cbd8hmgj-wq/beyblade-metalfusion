import unittest

from src.custom_blader.custom_state import CustomBladerState
from src.custom_blader.native_layout import (
    STATE_OFFSETS,
    STATE_SIZE,
    parse_state_bytes,
    serialize_state_bytes,
)


class NativeLayoutTests(unittest.TestCase):
    def distinct_state(self):
        return CustomBladerState(
            schema_version=1,
            initialized=1,
            player_name="Rin-7",
            bey_name="Nova Core",
            avatar_id=1,
            portrait_id=2,
            skin_palette_id=3,
            hair_style_id=1,
            hair_palette_id=2,
            outfit_palette_id=3,
            origin_id=2,
            tendency_id=1,
            blank_core_state=0,
            blank_core_id=0xF0,
            current_template_id=7,
            attack_ring_id=11,
            weight_disk_id=12,
            spin_gear_id=13,
            blade_base_id=14,
            future_flags=0x55,
        )

    def test_layout_has_stable_size_and_offsets(self):
        self.assertEqual(STATE_SIZE, 48)
        self.assertEqual(STATE_OFFSETS["schema_version"], 0)
        self.assertEqual(STATE_OFFSETS["initialized"], 1)
        self.assertEqual(STATE_OFFSETS["player_name"], 2)
        self.assertEqual(STATE_OFFSETS["bey_name"], 14)
        self.assertEqual(STATE_OFFSETS["avatar_id"], 26)
        self.assertEqual(STATE_OFFSETS["future_flags"], 41)
        self.assertEqual(STATE_OFFSETS["validation"], 44)

    def test_state_bytes_round_trip_every_distinct_field(self):
        state = self.distinct_state()
        raw = serialize_state_bytes(state)
        self.assertEqual(len(raw), STATE_SIZE)
        parsed = parse_state_bytes(raw)
        self.assertEqual(parsed.to_dict(), state.to_dict())

    def test_state_parser_rejects_wrong_size(self):
        with self.assertRaisesRegex(ValueError, "48 bytes"):
            parse_state_bytes(b"\x00" * 47)

    def test_state_parser_rejects_invalid_validation_word(self):
        raw = bytearray(serialize_state_bytes(self.distinct_state()))
        raw[STATE_OFFSETS["validation"]] ^= 0x01
        with self.assertRaisesRegex(ValueError, "validation"):
            parse_state_bytes(bytes(raw))


if __name__ == "__main__":
    unittest.main()
