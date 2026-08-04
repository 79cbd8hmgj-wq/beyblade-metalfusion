"""Byte-preserving primitives for G-Revolution event data.

The retail data mixes 32-bit command words and records whose final field is an
inline, NUL-terminated identifier.  Semantic names are deliberately not
invented here: callers retain every unknown byte.
"""
from __future__ import annotations
from dataclasses import dataclass
import struct

ROM_BASE = 0x08000000

def normalize_rom_pointer(value: int, rom_size: int) -> int:
    offset = value - ROM_BASE
    if not 0 <= offset < rom_size:
        raise ValueError(f"pointer 0x{value:08X} is outside ROM")
    return offset

@dataclass(frozen=True)
class InlineNamedRecord:
    offset: int
    fields: tuple[int, ...]
    name: str
    padding: bytes = b""

    @classmethod
    def parse(cls, data: bytes, offset: int, field_count: int = 3) -> "InlineNamedRecord":
        header = field_count * 4
        if offset < 0 or offset + header > len(data): raise ValueError("truncated record header")
        end = data.find(b"\0", offset + header)
        if end < 0: raise ValueError("unterminated record name")
        aligned = (end + 1 + 3) & ~3
        if aligned > len(data): raise ValueError("truncated record padding")
        raw = data[offset + header:end]
        try: name = raw.decode("ascii")
        except UnicodeDecodeError as exc: raise ValueError("record name is not ASCII") from exc
        fields = struct.unpack_from("<" + "I" * field_count, data, offset)
        return cls(offset, fields, name, data[end + 1:aligned])

    def to_bytes(self) -> bytes:
        raw = struct.pack("<" + "I" * len(self.fields), *self.fields) + self.name.encode("ascii") + b"\0"
        need = (-len(raw)) & 3
        if len(self.padding) != need: raise ValueError("padding length does not match alignment")
        return raw + self.padding

@dataclass(frozen=True)
class WordCommand:
    offset: int
    value: int
    raw: bytes

def decode_words(data: bytes, offset: int = 0, size: int | None = None) -> list[WordCommand]:
    size = len(data) - offset if size is None else size
    if offset < 0 or size < 0 or offset + size > len(data) or size % 4: raise ValueError("invalid word-stream extent")
    return [WordCommand(p, struct.unpack_from("<I", data, p)[0], data[p:p+4]) for p in range(offset, offset+size, 4)]

def encode_words(commands: list[WordCommand]) -> bytes:
    return b"".join(c.raw for c in commands)
