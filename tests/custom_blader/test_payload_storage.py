import importlib
import importlib.util
import unittest

from src.custom_blader.custom_save import SLOT_SIZE, parse_slot, serialize_slot
from src.custom_blader.custom_state import default_state
from tools.gba.save_format import PAYLOAD_SIZE, checksum


MODULE_NAME = "src.custom_blader.payload_storage"


class PayloadStorageTests(unittest.TestCase):
    def module(self):
        if importlib.util.find_spec(MODULE_NAME) is None:
            self.skipTest("payload_storage production module is not implemented yet")
        return importlib.import_module(MODULE_NAME)

    def test_payload_storage_module_exists(self):
        self.assertIsNotNone(
            importlib.util.find_spec(MODULE_NAME),
            "implement src.custom_blader.payload_storage",
        )

    def test_slot_offsets_use_first_32_retail_record_padding_pairs(self):
        storage = self.module()
        offsets = storage.slot_offsets()
        expected = tuple(
            storage.PADDING_TABLE_BASE
            + record_index * storage.PADDING_RECORD_STRIDE
            + storage.PADDING_DATA_SIZE
            + byte_index
            for record_index in range(storage.CUSTOM_SLOT_RECORDS)
            for byte_index in range(storage.PADDING_SIZE_PER_RECORD)
        )
        self.assertEqual(offsets, expected)
        self.assertEqual(len(offsets), SLOT_SIZE)
        self.assertEqual(len(set(offsets)), SLOT_SIZE)
        self.assertEqual(offsets[0], 0x02F2)
        self.assertEqual(offsets[-1], 0x0467)

    def test_distinct_slot_bytes_round_trip_through_sparse_payload_mapping(self):
        storage = self.module()
        payload = bytes([0xA5]) * PAYLOAD_SIZE
        slot = bytes(range(SLOT_SIZE))
        encoded = storage.embed_slot(payload, slot)
        self.assertEqual(storage.extract_slot(encoded), slot)

    def test_embedding_changes_only_the_mapped_padding_bytes(self):
        storage = self.module()
        payload = bytes((index * 37 + 11) & 0xFF for index in range(PAYLOAD_SIZE))
        slot = bytes((255 - index) & 0xFF for index in range(SLOT_SIZE))
        encoded = storage.embed_slot(payload, slot)
        mapped = set(storage.slot_offsets())
        changed = {index for index, pair in enumerate(zip(payload, encoded)) if pair[0] != pair[1]}
        expected_changed = {
            offset
            for offset, value in zip(storage.slot_offsets(), slot)
            if payload[offset] != value
        }
        self.assertEqual(changed, expected_changed)
        self.assertTrue(changed <= mapped)
        self.assertEqual(len(encoded), PAYLOAD_SIZE)

    def test_zero_filled_retail_padding_loads_default_state(self):
        storage = self.module()
        payload = bytes(PAYLOAD_SIZE)
        raw = storage.extract_slot(payload)
        valid, _, state, status = parse_slot(raw)
        self.assertFalse(valid)
        self.assertIsNone(state)
        self.assertEqual(status, "missing magic")

        loaded, sequence, load_status = storage.load_state(payload)
        self.assertEqual(loaded.to_dict(), default_state().to_dict())
        self.assertEqual(sequence, 0)
        self.assertEqual(load_status, "default: missing magic")

    def test_state_embedding_uses_existing_slot_format_and_payload_checksum(self):
        storage = self.module()
        payload = bytes(PAYLOAD_SIZE)
        state = default_state()
        state.player_name = "Ari"
        state.bey_name = "Nova"
        encoded = storage.embed_state(payload, state, sequence=7)

        raw = storage.extract_slot(encoded)
        self.assertEqual(raw, serialize_slot(state, 7))
        valid, sequence, parsed, status = parse_slot(raw)
        self.assertTrue(valid, status)
        self.assertEqual(sequence, 7)
        self.assertEqual(parsed.to_dict(), state.to_dict())
        self.assertNotEqual(checksum(encoded), checksum(payload))

    def test_invalid_payload_and_slot_lengths_are_rejected(self):
        storage = self.module()
        with self.assertRaisesRegex(ValueError, "payload must be exactly"):
            storage.extract_slot(bytes(PAYLOAD_SIZE - 1))
        with self.assertRaisesRegex(ValueError, "payload must be exactly"):
            storage.embed_slot(bytes(PAYLOAD_SIZE + 1), bytes(SLOT_SIZE))
        with self.assertRaisesRegex(ValueError, "slot must be exactly"):
            storage.embed_slot(bytes(PAYLOAD_SIZE), bytes(SLOT_SIZE - 1))


if __name__ == "__main__":
    unittest.main()
