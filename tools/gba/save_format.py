"""Byte-preserving model of G-Revolution's 64-Kbit EEPROM save.

The Nintendo EEPROM routines transfer each logical eight-byte block most-
significant byte first. mGBA's raw ``.sav`` file therefore stores every block
with its bytes reversed relative to the little-endian structures used by the
game. ``SaveImage`` exposes logical header/payload/tail bytes while parsing and
emitting the physical emulator representation losslessly.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
from dataclasses import dataclass
from pathlib import Path

ROM_SHA256 = "c4a568adc896bace0e25dbff4aa0c1802933c88e3f4a4e825075116c8c4173e5"
EEPROM_SIZE = 0x2000
BLOCK_SIZE = 8
BLOCK_COUNT = 0x400
HEADER_SIZE = 0x18
PAYLOAD_SIZE = 0x1F60
PAYLOAD_BLOCK_FIRST = 3
PAYLOAD_BLOCK_LAST = 0x3EE
TAIL_OFFSET = 0x1F78
MAGIC = 0xFEEDFACE
CONSTANT_WORDS = (0x00370053, 0x00F6009C)
SIGNATURE = b"EEPROM_V124\0"
SIGNATURE_OFFSET = 0x3A93BC


class SaveFormatError(ValueError):
    pass


def _reverse_blocks(data: bytes) -> bytes:
    if len(data) % BLOCK_SIZE:
        raise SaveFormatError(
            f"EEPROM data length must be a multiple of {BLOCK_SIZE} bytes"
        )
    return b"".join(
        data[offset : offset + BLOCK_SIZE][::-1]
        for offset in range(0, len(data), BLOCK_SIZE)
    )


def physical_to_logical(data: bytes) -> bytes:
    """Convert mGBA/raw EEPROM block order to game-structure byte order."""
    return _reverse_blocks(data)


def logical_to_physical(data: bytes) -> bytes:
    """Convert game-structure byte order to mGBA/raw EEPROM block order."""
    return _reverse_blocks(data)


def checksum(payload: bytes) -> int:
    if len(payload) != PAYLOAD_SIZE:
        raise SaveFormatError(f"payload must be 0x{PAYLOAD_SIZE:X} bytes")
    return sum(
        struct.unpack_from("<I", payload, offset)[0]
        for offset in range(4, PAYLOAD_SIZE, 4)
    ) & 0xFFFFFFFF


@dataclass(frozen=True)
class Header:
    magic: int
    payload_checksum: int
    unknown_08: int
    unknown_0c: int
    constant_10: int
    constant_14: int

    @classmethod
    def parse(cls, data: bytes):
        if len(data) != HEADER_SIZE:
            raise SaveFormatError("header must be 24 bytes")
        return cls(*struct.unpack("<6I", data))

    def to_bytes(self) -> bytes:
        return struct.pack(
            "<6I",
            self.magic,
            self.payload_checksum,
            self.unknown_08,
            self.unknown_0c,
            self.constant_10,
            self.constant_14,
        )

    def validation(self, payload: bytes | None = None) -> dict:
        checks = {
            "magic": self.magic == MAGIC,
            "constants": (self.constant_10, self.constant_14) == CONSTANT_WORDS,
        }
        if payload is not None:
            calculated = checksum(payload)
            checks.update(
                header_checksum=self.payload_checksum == calculated,
                payload_checksum=struct.unpack_from("<I", payload)[0] == calculated,
            )
        checks["valid"] = all(checks.values())
        return checks


@dataclass(frozen=True)
class SaveImage:
    """Logical save structures backed by the physical mGBA EEPROM format."""

    header: Header
    payload: bytes
    tail: bytes

    @classmethod
    def parse(cls, data: bytes, allow_padding: bool = False):
        if (
            allow_padding
            and len(data) > EEPROM_SIZE
            and all(value in (0, 0xFF) for value in data[EEPROM_SIZE:])
        ):
            data = data[:EEPROM_SIZE]
        if len(data) != EEPROM_SIZE:
            raise SaveFormatError(
                f"save must be exactly 0x{EEPROM_SIZE:X} bytes"
            )
        logical = physical_to_logical(data)
        return cls(
            Header.parse(logical[:HEADER_SIZE]),
            logical[HEADER_SIZE:TAIL_OFFSET],
            logical[TAIL_OFFSET:],
        )

    def logical_bytes(self) -> bytes:
        output = self.header.to_bytes() + self.payload + self.tail
        if len(output) != EEPROM_SIZE:
            raise SaveFormatError("invalid preserved ranges")
        return output

    def to_bytes(self) -> bytes:
        return logical_to_physical(self.logical_bytes())

    def report(self) -> dict:
        return {
            "format": "beyblade-g-revolution-eeprom-v1",
            "size": EEPROM_SIZE,
            "physical_storage": {
                "block_size": BLOCK_SIZE,
                "block_byte_order": "reversed_relative_to_logical_structures",
                "emulator": "mGBA raw .sav",
            },
            "header": {
                **self.header.__dict__,
                "validation": self.header.validation(self.payload),
            },
            "payload": {
                "offset": HEADER_SIZE,
                "size": len(self.payload),
                "stored_checksum": struct.unpack_from("<I", self.payload)[0],
                "calculated_checksum": checksum(self.payload),
            },
            "tail": {
                "offset": TAIL_OFFSET,
                "size": len(self.tail),
                "classification": "unreferenced_candidate",
                "sha256": hashlib.sha256(self.tail).hexdigest(),
            },
        }


def inventory_bit(payload: bytes, offset: int, item_id: int, count: int) -> bool:
    if not 0 <= item_id < count:
        raise SaveFormatError("invalid component ID")
    if offset < 0 or offset + (count + 7) // 8 > len(payload):
        raise SaveFormatError("inventory bitfield out of bounds")
    return bool(payload[offset + item_id // 8] & (1 << (item_id % 8)))


def validate_rom(data: bytes, override: bool = False):
    digest = hashlib.sha256(data).hexdigest()
    if digest != ROM_SHA256 and not override:
        raise SaveFormatError(f"unsupported ROM SHA-256: {digest}")
    hits = []
    start = 0
    while True:
        offset = data.find(SIGNATURE, start)
        if offset < 0:
            break
        hits.append(offset)
        start = offset + 1
    if hits != [SIGNATURE_OFFSET]:
        raise SaveFormatError(
            f"EEPROM signature starts were {[hex(value) for value in hits]}"
        )
    return digest


def static_report(data: bytes, override: bool = False) -> dict:
    digest = validate_rom(data, override)
    return {
        "rom_sha256": digest,
        "signature": {
            "text": "EEPROM_V124",
            "rom_offset": "0x003A93BC",
            "runtime_address": "0x083A93BC",
            "confidence": "confirmed",
        },
        "eeprom": {
            "capacity_bytes": EEPROM_SIZE,
            "blocks": BLOCK_COUNT,
            "block_size": BLOCK_SIZE,
            "raw_save_block_byte_order": "reversed",
            "confidence": "confirmed",
        },
        "ranges": [
            {
                "blocks": "0x000-0x002",
                "offset": "0x0000",
                "size": "0x18",
                "purpose": "transaction_header",
            },
            {
                "blocks": "0x003-0x3EE",
                "offset": "0x0018",
                "size": "0x1F60",
                "purpose": "serialized_payload",
            },
            {
                "blocks": "0x3EF-0x3FF",
                "offset": "0x1F78",
                "size": "0x88",
                "purpose": "unreferenced_candidate",
            },
        ],
    }


def write_copy(source: Path, destination: Path, image: SaveImage):
    if source.resolve() == destination.resolve():
        raise SaveFormatError("refusing in-place write")
    destination.write_bytes(image.to_bytes())


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--rom")
    parser.add_argument("--save")
    parser.add_argument("--output", required=True)
    parser.add_argument("--research-override", action="store_true")
    parser.add_argument("--allow-padding", action="store_true")
    parser.add_argument("--custom-extension", action="store_true")
    arguments = parser.parse_args(argv)
    if bool(arguments.rom) == bool(arguments.save):
        parser.error("choose exactly one of --rom or --save")
    if arguments.rom:
        result = static_report(
            Path(arguments.rom).read_bytes(),
            arguments.research_override,
        )
    else:
        save_data = Path(arguments.save).read_bytes()
        result = SaveImage.parse(save_data, arguments.allow_padding).report()
        if arguments.custom_extension:
            from .custom_save_extension import extension_report

            result["custom_extension"] = extension_report(save_data)
    output = Path(arguments.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
