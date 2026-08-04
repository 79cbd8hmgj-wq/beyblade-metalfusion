import unittest

from src.custom_blader.custom_save import (
    SLOT_SIZE,
    parse_slot,
    select_newest,
    serialize_slot,
    simulate_slot_transaction,
)
from src.custom_blader.custom_state import CustomBladerState, default_state


class CustomSaveTransactionTests(unittest.TestCase):
    def state(self, name, marker):
        return CustomBladerState(
            initialized=1,
            player_name=name,
            bey_name=f"Bey{marker}",
            avatar_id=marker % 4,
            portrait_id=(marker + 1) % 4,
            skin_palette_id=(marker + 2) % 4,
            hair_style_id=marker % 4,
            hair_palette_id=(marker + 3) % 4,
            outfit_palette_id=(marker + 1) % 4,
            origin_id=(marker + 2) % 4,
            tendency_id=(marker + 3) % 4,
            blank_core_state=0,
            blank_core_id=0xF0,
            current_template_id=20 + marker,
            attack_ring_id=30 + marker,
            weight_disk_id=10 + marker,
            spin_gear_id=5 + marker,
            blade_base_id=15 + marker,
            future_flags=0x40 + marker,
        )

    def test_slot_round_trip_preserves_distinct_component_and_future_fields(self):
        state = self.state("Rin", 3)
        raw = serialize_slot(state, 0x12345678)
        valid, sequence, parsed, message = parse_slot(raw)
        self.assertTrue(valid, message)
        self.assertEqual(sequence, 0x12345678)
        self.assertEqual(parsed.to_dict(), state.to_dict())

    def test_half_range_sequence_difference_is_ambiguous_and_prefers_slot_a(self):
        a = serialize_slot(self.state("Alpha", 1), 0)
        b = serialize_slot(self.state("Beta", 2), 0x80000000)
        selected = select_newest(a, b)
        self.assertEqual(selected[0], "A")
        self.assertEqual(selected[2].player_name, "Alpha")

    def test_interrupted_write_never_loads_partial_new_state(self):
        old_state = self.state("Old", 1)
        new_state = self.state("New", 2)
        slot_a = serialize_slot(old_state, 10)
        slot_b = bytes(SLOT_SIZE)
        for interrupt_after_block in range(0, 9):
            next_a, next_b = simulate_slot_transaction(
                slot_a,
                slot_b,
                new_state,
                interrupt_after_block=interrupt_after_block,
            )
            selected = select_newest(next_a, next_b)
            self.assertIn(selected[2].player_name, {"Old", "New"})
            if selected[2].player_name == "New":
                self.assertEqual(selected[2].to_dict(), new_state.to_dict())
            else:
                self.assertEqual(selected[2].to_dict(), old_state.to_dict())

    def test_complete_write_selects_new_state(self):
        old_state = default_state()
        old_state.player_name = "Old"
        new_state = default_state()
        new_state.player_name = "New"
        slot_a = serialize_slot(old_state, 0xFFFFFFFE)
        slot_b = bytes(SLOT_SIZE)
        next_a, next_b = simulate_slot_transaction(
            slot_a,
            slot_b,
            new_state,
            interrupt_after_block=None,
        )
        selected = select_newest(next_a, next_b)
        self.assertEqual(selected[2].player_name, "New")
        self.assertEqual(selected[1], 0xFFFFFFFF)


if __name__ == "__main__":
    unittest.main()
