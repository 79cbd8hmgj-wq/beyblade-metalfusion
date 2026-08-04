#!/usr/bin/env python3
"""Create a tiny valid GBA ROM used only for debugger smoke testing."""

from __future__ import annotations

import argparse
from pathlib import Path

NINTENDO_LOGO = bytes.fromhex(
    "24ffae51699aa2213d84820a84e409ad11248b98c0817f21a352be199309ce20"
    "10464a4af82731ec58c7e83382e3cebf85f4df94ce4b09c194568ac01372a7fc"
    "9f844d73a3ca9a615897a327fc039876231dc7610304ae56bf38840040a70efd"
    "ff52fe036f9530f197fbc08560d68025a963be03014e38e2f9a234ffbb3e0344"
    "780090cb88113a9465c07c6387f03cafd625e48b380aac7221d4f807"
)


def build_rom() -> bytes:
    if len(NINTENDO_LOGO) != 156:
        raise ValueError(f"Nintendo logo must be 156 bytes, got {len(NINTENDO_LOGO)}")

    rom = bytearray([0xFF] * 0x200)
    rom[0x000:0x004] = (0xEA00002E).to_bytes(4, "little")
    rom[0x004:0x0A0] = NINTENDO_LOGO
    rom[0x0A0:0x0AC] = b"MGBA GDBTEST"
    rom[0x0AC:0x0B0] = b"GDBG"
    rom[0x0B0:0x0B2] = b"00"
    rom[0x0B2] = 0x96
    rom[0x0B3] = 0x00
    rom[0x0B4] = 0x00
    rom[0x0B5:0x0BC] = bytes(7)
    rom[0x0BC] = 0x00

    checksum = 0
    for value in rom[0x0A0:0x0BD]:
        checksum = (checksum - value) & 0xFF
    rom[0x0BD] = (checksum - 0x19) & 0xFF
    rom[0x0BE:0x0C0] = bytes(2)

    rom[0x0C0:0x0C4] = (0xEAFFFFFE).to_bytes(4, "little")
    return bytes(rom)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.write_bytes(build_rom())
    print(f"Wrote {args.output} ({args.output.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
