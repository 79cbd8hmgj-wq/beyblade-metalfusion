import importlib
import importlib.util
import unittest

from tools.gba.save_format import PAYLOAD_SIZE


MODULE_NAME = "tools.gba.save_copy_map"


def confirmed_untouched_offsets():
    offsets = set(range(0x0000, 0x0004))
    offsets.update(range(0x0054, 0x0058))
    offsets.add(0x02E7)
    for record_index in range(83):
        start = 0x02E8 + record_index * 0x0C + 0x0A
        offsets.update((start, start + 1))
    offsets.add(0x1F5F)
    return offsets


class SaveCopyMapTests(unittest.TestCase):
    def module(self):
        if importlib.util.find_spec(MODULE_NAME) is None:
            self.skipTest("save_copy_map production module is not implemented yet")
        return importlib.import_module(MODULE_NAME)

    def test_save_copy_map_module_exists(self):
        self.assertIsNotNone(
            importlib.util.find_spec(MODULE_NAME),
            "implement tools.gba.save_copy_map",
        )

    def test_intersection_requires_every_seed_and_mode_to_preserve_an_offset(self):
        copy_map = self.module()
        preserved = confirmed_untouched_offsets()
        runs = []
        for seed, mode in ((0xA5, 0), (0x5A, 0), (0x3C, 1)):
            before = bytes([seed]) * PAYLOAD_SIZE
            after = bytearray(before)
            for offset in range(PAYLOAD_SIZE):
                if offset not in preserved:
                    after[offset] = (seed + mode + offset + 1) & 0xFF
                    if after[offset] == seed:
                        after[offset] ^= 0xFF
            runs.append((before, bytes(after)))

        self.assertEqual(copy_map.intersect_unchanged_offsets(runs), preserved)

    def test_coalesced_ranges_are_end_exclusive_and_deterministic(self):
        copy_map = self.module()
        self.assertEqual(
            copy_map.coalesce_offsets({8, 2, 1, 0, 5, 9}),
            [
                {"start": 0, "end_exclusive": 3, "size": 3},
                {"start": 5, "end_exclusive": 6, "size": 1},
                {"start": 8, "end_exclusive": 10, "size": 2},
            ],
        )

    def test_confirmed_padding_pairs_match_all_83_record_tails(self):
        copy_map = self.module()
        offsets = copy_map.record_padding_offsets()
        self.assertEqual(len(offsets), 166)
        self.assertEqual(offsets[0:2], (0x02F2, 0x02F3))
        self.assertEqual(offsets[-2:], (0x06CA, 0x06CB))
        self.assertEqual(set(offsets) <= confirmed_untouched_offsets(), True)

    def test_report_separates_checksum_holes_record_padding_and_trailing_byte(self):
        copy_map = self.module()
        report = copy_map.confirmed_runtime_report()
        self.assertEqual(report["serializer"], "0x08045198")
        self.assertEqual(report["deserializer"], "0x08045590")
        self.assertEqual(report["payload_size"], "0x1F60")
        self.assertEqual(report["preserved_byte_count"], 176)
        self.assertEqual(report["record_table"]["base"], "0x02E8")
        self.assertEqual(report["record_table"]["count"], 83)
        self.assertEqual(report["record_table"]["stride"], "0x0C")
        self.assertEqual(report["record_table"]["serialized_bytes_per_record"], 10)
        self.assertEqual(report["record_table"]["padding_bytes_per_record"], 2)
        self.assertEqual(report["custom_slot"]["record_count"], 32)
        self.assertEqual(report["custom_slot"]["size"], 64)
        self.assertEqual(report["custom_slot"]["first_payload_offset"], "0x02F2")
        self.assertEqual(report["custom_slot"]["last_payload_offset"], "0x0467")
        self.assertFalse(report["eeprom_tail_required"])

    def test_mismatched_or_truncated_runs_are_rejected(self):
        copy_map = self.module()
        with self.assertRaisesRegex(ValueError, "at least one"):
            copy_map.intersect_unchanged_offsets([])
        with self.assertRaisesRegex(ValueError, "same length"):
            copy_map.intersect_unchanged_offsets([(b"abc", b"ab")])
        with self.assertRaisesRegex(ValueError, "0x1F60"):
            copy_map.intersect_unchanged_offsets([(b"abc", b"xyz")])


if __name__ == "__main__":
    unittest.main()
