"""Task 3 component-name tables and complete-template configuration.

The four confirmed name arrays are stored language-major: five consecutive
arrays of ``count`` little-endian pointers.  No ROM-writing API is provided.
"""
from __future__ import annotations
from dataclasses import dataclass
import struct

ROM_BASE = 0x08000000
LANGUAGES = ("english", "french", "german", "italian", "spanish")

@dataclass(frozen=True)
class Category:
    slug: str
    offset: int
    count: int
    confidence: str = "confirmed"

    @property
    def end(self) -> int:
        return self.offset + self.count * len(LANGUAGES) * 4

CATEGORIES = (
    Category("spin-gears", 0x0007AF0C, 22),
    Category("attack-rings", 0x0007B0D8, 77),
    Category("blade-bases", 0x0007B824, 42),
    Category("weight-disks", 0x0007BC28, 19),
)
CATEGORY_BY_SLUG = {c.slug: c for c in CATEGORIES}

@dataclass(frozen=True)
class ComponentName:
    category: str
    local_id: int
    source_offset: int
    pointers: tuple[int, ...]
    names: tuple[str, ...]

def _string(rom: bytes, pointer: int) -> str:
    off = pointer - ROM_BASE
    if not 0 <= off < len(rom):
        raise ValueError(f"pointer 0x{pointer:08X} outside ROM")
    end = rom.find(b"\0", off)
    if end < 0:
        raise ValueError(f"unterminated string at 0x{off:08X}")
    return rom[off:end].decode("ascii")

def extract_category(rom: bytes, category: str) -> list[ComponentName]:
    try:
        spec = CATEGORY_BY_SLUG[category]
    except KeyError as exc:
        raise ValueError(f"invalid component category: {category}") from exc
    if len(rom) < spec.end:
        raise ValueError(f"truncated ROM: need through 0x{spec.end:08X}")
    result = []
    for item_id in range(spec.count):
        ptrs = tuple(struct.unpack_from("<I", rom, spec.offset + 4*(lang*spec.count+item_id))[0]
                     for lang in range(len(LANGUAGES)))
        result.append(ComponentName(category, item_id, spec.offset + 4*item_id,
                                    ptrs, tuple(_string(rom, p) for p in ptrs)))
    return result

def serialize_pointer_arrays(entries: list[ComponentName]) -> bytes:
    """Serialize one parsed category to its original language-major bytes."""
    if not entries:
        raise ValueError("component category cannot be empty")
    if [x.local_id for x in entries] != list(range(len(entries))):
        raise ValueError("component IDs must be contiguous and zero-based")
    out = bytearray()
    for lang in range(len(LANGUAGES)):
        for entry in entries:
            if len(entry.pointers) != len(LANGUAGES):
                raise ValueError("each entry requires five pointers")
            out += struct.pack("<I", entry.pointers[lang])
    return bytes(out)

def decode_template_configuration(raw: bytes) -> dict[str, int]:
    """Decode the evidence-backed fields at template offsets 0x1C..0x23."""
    if len(raw) != 8:
        raise ValueError("packed configuration must be 8 bytes")
    return {
        "field_1c_u8": raw[0],
        "attack_ring_id": raw[1],
        "weight_disk_id": raw[2],
        "spin_gear_packed": raw[3],
        "blade_base_id": raw[4],
        "bit_chip_id": raw[5],
        "field_22_u8": raw[6],
        "field_23_u8": raw[7],
    }

