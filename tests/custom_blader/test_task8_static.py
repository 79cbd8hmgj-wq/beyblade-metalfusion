import struct
import unittest

from tools.gba.task8_static import (
    find_pointer_references,
    find_thumb_function_start,
    find_thumb_literal_loads,
    scan_anchor,
)


class Task8StaticScannerTests(unittest.TestCase):
    def test_pointer_references_are_sorted_and_include_unaligned_sites(self):
        data = bytearray(64)
        pointer = 0x08000020
        data[3:7] = struct.pack("<I", pointer)
        data[24:28] = struct.pack("<I", pointer)
        self.assertEqual(find_pointer_references(bytes(data), pointer), [3, 24])

    def test_thumb_literal_load_resolves_pointer_pool(self):
        data = bytearray(0x80)
        # At 0x10: ldr r2, [pc, #0x0c] -> aligned PC 0x14 + 0x0c = 0x20.
        struct.pack_into("<H", data, 0x10, 0x4A03)
        struct.pack_into("<I", data, 0x20, 0x08001234)
        loads = find_thumb_literal_loads(bytes(data), 0x20)
        self.assertEqual(loads, [{"instruction_offset": 0x10, "register": 2}])

    def test_function_start_prefers_push_with_link_register(self):
        data = bytearray(0x80)
        struct.pack_into("<H", data, 0x20, 0xB510)
        struct.pack_into("<H", data, 0x2A, 0x4A03)
        self.assertEqual(find_thumb_function_start(bytes(data), 0x2A), 0x20)

    def test_scan_anchor_chains_string_pointer_literal_and_function(self):
        data = bytearray(0x200)
        string_offset = 0x180
        data[string_offset:string_offset + 11] = b"Enter name\0"
        table_offset = 0x100
        struct.pack_into("<I", data, table_offset, 0x08000000 + string_offset)
        literal_offset = 0x60
        struct.pack_into("<I", data, literal_offset, 0x08000000 + table_offset)
        struct.pack_into("<H", data, 0x40, 0xB510)
        # 0x50: aligned PC 0x54, literal at 0x60 => imm8=3, r1.
        struct.pack_into("<H", data, 0x50, 0x4903)

        result = scan_anchor(bytes(data), "enter-name", string_offset)

        self.assertEqual(result["text"], "Enter name")
        self.assertEqual(result["direct_pointer_references"], [table_offset])
        self.assertEqual(result["table_pointer_references"], [literal_offset])
        self.assertEqual(result["code_references"][0]["instruction_offset"], 0x50)
        self.assertEqual(result["code_references"][0]["function_start"], 0x40)


if __name__ == "__main__":
    unittest.main()
