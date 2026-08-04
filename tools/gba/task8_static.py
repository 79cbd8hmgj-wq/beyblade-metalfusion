"""Focused static analysis for Task 8 Custom Blader hook candidates."""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path

ROM_BASE = 0x08000000
SUPPORTED_SHA256 = "c4a568adc896bace0e25dbff4aa0c1802933c88e3f4a4e825075116c8c4173e5"

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
    """Find nearby structure starts whose addresses are loaded by Thumb code.

    Localized text pointers are frequently fields in menu descriptors rather
    than direct literal-pool values. This keeps the relationship structural and
    does not assign a semantic type to the descriptor.
    """
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


def scan_task8(data: bytes) -> dict:
    digest = hashlib.sha256(data).hexdigest()
    if digest != SUPPORTED_SHA256:
        raise ValueError(f"unsupported ROM SHA-256: {digest}")
    return {
        "schema_version": 1,
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
