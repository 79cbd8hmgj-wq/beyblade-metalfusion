"""Focused static analysis for Task 8 Custom Blader hook candidates."""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path

ROM_BASE = 0x08000000
SUPPORTED_SHA256 = "c4a568adc896bace0e25dbff4aa0c1802933c88e3f4a4e825075116c8c4173e5"
SCENE_DESCRIPTOR_TABLE = 0x000BA1A8
SCENE_DESCRIPTOR_COUNT = 55
SCENE_DESCRIPTOR_SIZE = 0x50
MAIN_MENU_SCENE_INDEX = 3
NAME_ENTRY_SCENE_INDEX = 10

KNOWN_ANCHORS = {
    "new-game": 0x003A3150,
    "name-label": 0x003A34F0,
    "enter-name": 0x003A3760,
    "takao": 0x0033BF84,
    "tyson": 0x0033BF8C,
}


def _u16(data: bytes, offset: int) -> int:
    if offset < 0 or offset + 2 > len(data):
        raise ValueError("halfword outside ROM")
    return struct.unpack_from("<H", data, offset)[0]


def _u32(data: bytes, offset: int) -> int:
    if offset < 0 or offset + 4 > len(data):
        raise ValueError("word outside ROM")
    return struct.unpack_from("<I", data, offset)[0]


def _read_c_string(data: bytes, offset: int, maximum: int = 256) -> str:
    if not 0 <= offset < len(data):
        raise ValueError("string offset outside ROM")
    end = data.find(b"\0", offset, min(len(data), offset + maximum))
    if end < 0:
        raise ValueError("unterminated anchor string")
    try:
        return data[offset:end].decode("ascii", "strict")
    except UnicodeDecodeError as exc:
        raise ValueError("anchor is not ASCII") from exc


def _rom_pointer_to_offset(pointer: int, data_length: int, *, label: str) -> int:
    if not ROM_BASE <= pointer < ROM_BASE + data_length:
        raise ValueError(f"{label} outside ROM: 0x{pointer:08X}")
    return pointer - ROM_BASE


def _find_u32(region: bytes, value: int) -> bool:
    return struct.pack("<I", value) in region


def find_pointer_references(data: bytes, value: int) -> list[int]:
    """Return every aligned or unaligned little-endian occurrence."""
    if not 0 <= value <= 0xFFFFFFFF:
        raise ValueError("pointer value outside u32")
    pattern = struct.pack("<I", value)
    references: list[int] = []
    cursor = 0
    while True:
        cursor = data.find(pattern, cursor)
        if cursor < 0:
            return references
        references.append(cursor)
        cursor += 1


def find_thumb_literal_loads(data: bytes, literal_offset: int) -> list[dict]:
    """Find Thumb-1 LDR literal instructions that resolve to one pool word."""
    if literal_offset < 0 or literal_offset + 4 > len(data):
        raise ValueError("literal offset outside ROM")
    loads: list[dict] = []
    for instruction_offset in range(0, len(data) - 1, 2):
        instruction = _u16(data, instruction_offset)
        if instruction & 0xF800 != 0x4800:
            continue
        immediate = (instruction & 0xFF) << 2
        resolved = ((instruction_offset + 4) & ~3) + immediate
        if resolved == literal_offset:
            loads.append(
                {
                    "instruction_offset": instruction_offset,
                    "register": (instruction >> 8) & 0x7,
                }
            )
    return loads


def find_thumb_function_start(data: bytes, instruction_offset: int, maximum_back: int = 0x400) -> int | None:
    """Find the nearest preceding Thumb PUSH that saves LR."""
    if not 0 <= instruction_offset < len(data):
        raise ValueError("instruction offset outside ROM")
    lower = max(0, instruction_offset - maximum_back)
    for offset in range(instruction_offset & ~1, lower - 1, -2):
        if _u16(data, offset) & 0xFF00 == 0xB500:
            return offset
    return None


def parse_scene_descriptor_table(
    data: bytes,
    table_offset: int,
    count: int,
    descriptor_size: int = SCENE_DESCRIPTOR_SIZE,
) -> list[dict]:
    """Parse an explicit pointer table of fixed 0x50-byte scene descriptors.

    The first 0x30 bytes are callback-like fields. Odd ROM pointers in those
    fields are decoded as Thumb callbacks, while every raw word is retained so
    resource and flag fields remain neutral.
    """
    if count <= 0:
        raise ValueError("descriptor count must be positive")
    if descriptor_size <= 0 or descriptor_size % 4:
        raise ValueError("descriptor size must be a positive multiple of four")
    if table_offset < 0 or table_offset + count * 4 > len(data):
        raise ValueError("descriptor table outside ROM")

    descriptors: list[dict] = []
    for index in range(count):
        pointer = _u32(data, table_offset + index * 4)
        descriptor_offset = _rom_pointer_to_offset(pointer, len(data), label="descriptor pointer")
        if descriptor_offset + descriptor_size > len(data):
            raise ValueError("descriptor extent outside ROM")
        words = list(struct.unpack_from(f"<{descriptor_size // 4}I", data, descriptor_offset))
        callbacks: list[dict] = []
        for field_offset, value in enumerate(words[: 0x30 // 4]):
            byte_offset = field_offset * 4
            if value == 0 or not value & 1:
                continue
            function_pointer = value & ~1
            if ROM_BASE <= function_pointer < ROM_BASE + len(data):
                callbacks.append(
                    {
                        "field_offset": byte_offset,
                        "pointer": value,
                        "function_offset": function_pointer - ROM_BASE,
                    }
                )
        descriptors.append(
            {
                "index": index,
                "pointer": pointer,
                "descriptor_offset": descriptor_offset,
                "words": words,
                "thumb_callbacks": callbacks,
            }
        )
    return descriptors


def analyze_name_symbol_contract(data: bytes, function_offset: int, size: int) -> dict:
    """Validate the retail name-entry symbol handler's bounded contract."""
    if function_offset < 0 or size <= 0 or function_offset + size > len(data):
        raise ValueError("name symbol function outside ROM")
    region = data[function_offset : function_offset + size]
    halfwords = {
        struct.unpack_from("<H", region, offset)[0]
        for offset in range(0, len(region) - 1, 2)
    }
    required = {
        0x2C07: "confirm key comparison",
        0x2C08: "delete key comparison",
        0x2C09: "case-toggle comparison",
        0x280E: "maximum-length comparison",
    }
    missing = [description for opcode, description in required.items() if opcode not in halfwords]
    if missing:
        raise ValueError("name symbol contract missing: " + ", ".join(missing))
    if not _find_u32(region, 0x030009A8):
        raise ValueError("name symbol contract missing case flag address")
    if not _find_u32(region, 0x030009AC):
        raise ValueError("name symbol contract missing buffer pointer address")
    return {
        "special_codes": {"confirm": 7, "delete": 8, "case_toggle": 9},
        "maximum_characters": 15,
        "storage_bytes_with_nul": 16,
        "case_flag_address": 0x030009A8,
        "buffer_pointer_address": 0x030009AC,
        "evidence": {
            "append_guard": "The handler appends only while the current length is <= 14.",
            "confirm_guard": "Special code 7 returns success only when the current length is greater than zero.",
        },
    }


def analyze_name_commit_contract(data: bytes, function_offset: int, size: int) -> dict:
    """Validate the retail name-entry commit target and copy width."""
    if function_offset < 0 or size <= 0 or function_offset + size > len(data):
        raise ValueError("name commit function outside ROM")
    region = data[function_offset : function_offset + size]
    halfwords = {
        struct.unpack_from("<H", region, offset)[0]
        for offset in range(0, len(region) - 1, 2)
    }
    if 0x2110 not in halfwords or 0x2210 not in halfwords:
        raise ValueError("name commit contract missing 16-byte clear/copy widths")
    if not _find_u32(region, 0x03000198):
        raise ValueError("name commit contract missing runtime base pointer")
    if not _find_u32(region, 0x00000858):
        raise ValueError("name commit contract missing runtime name offset")
    return {
        "runtime_base_pointer_address": 0x03000198,
        "runtime_name_offset": 0x858,
        "copy_size": 16,
        "behavior": "Clear 16 destination bytes, then copy 16 bytes from the name-entry buffer.",
    }


def _code_references(data: bytes, literal_offsets: list[int]) -> list[dict]:
    references: list[dict] = []
    for literal_offset in sorted(set(literal_offsets)):
        for load in find_thumb_literal_loads(data, literal_offset):
            references.append(
                {
                    **load,
                    "literal_offset": literal_offset,
                    "function_start": find_thumb_function_start(data, load["instruction_offset"]),
                }
            )
    return references


def _container_candidates(data: bytes, field_offset: int, maximum_back: int = 0x20) -> list[dict]:
    """Find nearby structure starts whose addresses are loaded by Thumb code."""
    candidates: list[dict] = []
    lower = max(0, field_offset - maximum_back)
    for candidate_offset in range(field_offset & ~3, lower - 1, -4):
        pointer_sites = find_pointer_references(data, ROM_BASE + candidate_offset)
        code = _code_references(data, pointer_sites)
        if code:
            candidates.append(
                {
                    "candidate_offset": candidate_offset,
                    "field_delta": field_offset - candidate_offset,
                    "pointer_references": pointer_sites,
                    "code_references": code,
                }
            )
    return candidates


def scan_anchor(data: bytes, anchor_id: str, string_offset: int) -> dict:
    text = _read_c_string(data, string_offset)
    direct = find_pointer_references(data, ROM_BASE + string_offset)
    table_pointer_references: list[int] = []
    code_references: list[dict] = []
    containers: list[dict] = []
    for direct_offset in direct:
        second_level = find_pointer_references(data, ROM_BASE + direct_offset)
        table_pointer_references.extend(second_level)
        code_references.extend(_code_references(data, second_level))
        containers.extend(_container_candidates(data, second_level[0]) if len(second_level) == 1 else [])
    return {
        "id": anchor_id,
        "text": text,
        "string_offset": string_offset,
        "runtime_address": ROM_BASE + string_offset,
        "direct_pointer_references": sorted(set(direct)),
        "table_pointer_references": sorted(set(table_pointer_references)),
        "code_references": sorted(
            code_references,
            key=lambda item: (item["instruction_offset"], item["literal_offset"]),
        ),
        "container_candidates": sorted(containers, key=lambda item: item["candidate_offset"]),
    }


def _compact_descriptor(descriptor: dict) -> dict:
    return {
        "index": descriptor["index"],
        "pointer": descriptor["pointer"],
        "descriptor_offset": descriptor["descriptor_offset"],
        "thumb_callbacks": descriptor["thumb_callbacks"],
        "tail_words": descriptor["words"][12:],
    }


def scan_task8(data: bytes) -> dict:
    digest = hashlib.sha256(data).hexdigest()
    if digest != SUPPORTED_SHA256:
        raise ValueError(f"unsupported ROM SHA-256: {digest}")
    descriptors = parse_scene_descriptor_table(
        data,
        SCENE_DESCRIPTOR_TABLE,
        SCENE_DESCRIPTOR_COUNT,
    )
    main_menu = descriptors[MAIN_MENU_SCENE_INDEX]
    name_entry = descriptors[NAME_ENTRY_SCENE_INDEX]
    name_symbol = analyze_name_symbol_contract(data, 0x00066B10, 0xB4)
    name_commit = analyze_name_commit_contract(data, 0x000668C8, 0xBC)
    return {
        "schema_version": 2,
        "rom_sha256": digest,
        "anchors": [scan_anchor(data, anchor_id, offset) for anchor_id, offset in KNOWN_ANCHORS.items()],
        "fixed_structures": {
            "protagonist_name_row": {
                "start": 0x00077F10,
                "end": 0x00077F24,
                "confidence": "strongly_supported",
            },
            "enter_name_localized_row": {
                "start": 0x00096D00,
                "end": 0x00096D14,
                "confidence": "confirmed",
            },
            "scene_descriptor_table": {
                "start": SCENE_DESCRIPTOR_TABLE,
                "count": SCENE_DESCRIPTOR_COUNT,
                "entry_width": 4,
                "descriptor_width": SCENE_DESCRIPTOR_SIZE,
                "descriptor_stride": SCENE_DESCRIPTOR_SIZE,
                "main_menu": _compact_descriptor(main_menu),
                "name_entry": _compact_descriptor(name_entry),
                "confidence": "confirmed",
            },
            "name_entry_contract": {
                "scene_index": NAME_ENTRY_SCENE_INDEX,
                "init_function": 0x0006645C,
                "update_function": 0x00066664,
                "draw_function": 0x000667EC,
                "selection_handler": 0x000668C8,
                "back_handler": 0x00066984,
                "symbol_handler": 0x00066B10,
                "symbol_contract": name_symbol,
                "commit_contract": name_commit,
                "confidence": "strongly_supported",
            },
        },
    }


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", required=True)
    parser.add_argument("--output", required=True)
    arguments = parser.parse_args(argv)
    rom_path = Path(arguments.rom)
    data = rom_path.read_bytes()
    report = scan_task8(data)
    output = Path(arguments.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
