import struct
import unittest

from tools.gba.task8_static import (
    analyze_name_commit_contract,
    analyze_name_symbol_contract,
    find_pointer_references,
    find_thumb_function_start,
    find_thumb_literal_loads,
    parse_scene_descriptor_table,
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

    def test_scene_descriptor_table_preserves_all_words_and_thumb_callbacks(self):
        data = bytearray(0x200)
        table_offset = 0x20
        descriptor_offset = 0x80
        struct.pack_into("<I", data, table_offset, 0x08000000 + descriptor_offset)
        words = [0] * 20
        words[0] = 0x08000101
        words[1] = 0x08000121
        words[18] = 0x0004001F
        words[19] = 0x000100FF
        struct.pack_into("<20I", data, descriptor_offset, *words)

        descriptors = parse_scene_descriptor_table(bytes(data), table_offset, 1)

        self.assertEqual(len(descriptors), 1)
        self.assertEqual(descriptors[0]["descriptor_offset"], descriptor_offset)
        self.assertEqual(descriptors[0]["words"], words)
        self.assertEqual(
            descriptors[0]["thumb_callbacks"],
            [
                {"field_offset": 0, "pointer": 0x08000101, "function_offset": 0x100},
                {"field_offset": 4, "pointer": 0x08000121, "function_offset": 0x120},
            ],
        )

    def test_scene_descriptor_table_rejects_out_of_rom_pointer(self):
        data = bytearray(0x100)
        struct.pack_into("<I", data, 0x20, 0x09000000)
        with self.assertRaisesRegex(ValueError, "descriptor pointer"):
            parse_scene_descriptor_table(bytes(data), 0x20, 1)

    def test_name_symbol_contract_detects_special_keys_limit_and_globals(self):
        data = bytearray(0x100)
        # cmp r4,#8; cmp r4,#7; cmp r4,#9; cmp r0,#14
        struct.pack_into("<4H", data, 0x10, 0x2C08, 0x2C07, 0x2C09, 0x280E)
        struct.pack_into("<I", data, 0x40, 0x030009A8)
        struct.pack_into("<I", data, 0x44, 0x030009AC)

        contract = analyze_name_symbol_contract(bytes(data), 0x10, 0x50)

        self.assertEqual(contract["special_codes"], {"confirm": 7, "delete": 8, "case_toggle": 9})
        self.assertEqual(contract["maximum_characters"], 15)
        self.assertEqual(contract["case_flag_address"], 0x030009A8)
        self.assertEqual(contract["buffer_pointer_address"], 0x030009AC)

    def test_name_commit_contract_detects_runtime_target_and_copy_size(self):
        data = bytearray(0x100)
        struct.pack_into("<I", data, 0x40, 0x03000198)
        struct.pack_into("<I", data, 0x44, 0x00000858)
        # movs r1,#16 and movs r2,#16
        struct.pack_into("<HH", data, 0x20, 0x2110, 0x2210)

        contract = analyze_name_commit_contract(bytes(data), 0x10, 0x50)

        self.assertEqual(contract["runtime_base_pointer_address"], 0x03000198)
        self.assertEqual(contract["runtime_name_offset"], 0x858)
        self.assertEqual(contract["copy_size"], 16)


if __name__ == "__main__":
    unittest.main()
