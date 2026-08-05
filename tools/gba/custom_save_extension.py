"""Experimental helpers for the unverified EEPROM-tail extension.

Task 8 now uses confirmed payload padding for native persistence. These tail
helpers remain available only for copied-save research and must preserve
mGBA's physical eight-byte block ordering.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from src.custom_blader.custom_save import (
    SLOT_SIZE,
    parse_slot,
    select_newest,
    serialize_slot,
)
from src.custom_blader.custom_state import CustomBladerState, sanitize

from .save_format import EEPROM_SIZE, TAIL_OFFSET, SaveFormatError, SaveImage

A0 = 0
B0 = 64
WARNING = (
    "WARNING: EEPROM tail extension is unverified; operate only on copied saves."
)


def extension_report(data: bytes) -> dict:
    image = SaveImage.parse(data, allow_padding=True)
    slot_a = image.tail[A0 : A0 + SLOT_SIZE]
    slot_b = image.tail[B0 : B0 + SLOT_SIZE]
    parsed_a = parse_slot(slot_a)
    parsed_b = parse_slot(slot_b)
    newest = select_newest(slot_a, slot_b)
    return {
        "tail_offset": f"0x{TAIL_OFFSET:04X}",
        "slot_a": {
            "blocks": "0x3EF-0x3F6",
            "valid": parsed_a[0],
            "sequence": parsed_a[1],
            "status": parsed_a[3],
        },
        "slot_b": {
            "blocks": "0x3F7-0x3FE",
            "valid": parsed_b[0],
            "sequence": parsed_b[1],
            "status": parsed_b[3],
        },
        "reserved_block": "0x3FF",
        "safety": "unverified",
        "selected": {
            "slot": newest[0],
            "sequence": newest[1],
            "state": newest[2].to_dict(),
        },
    }


def write_extension(
    source: Path,
    output: Path,
    state: CustomBladerState,
    sequence: int | None = None,
    allow_unverified: bool = False,
) -> None:
    if not allow_unverified:
        raise SaveFormatError(
            "refusing unverified EEPROM-tail edit without "
            "--allow-unverified-tail-extension"
        )
    if source.resolve() == output.resolve():
        raise SaveFormatError("refusing in-place custom extension edit")

    raw = source.read_bytes()
    if len(raw) < EEPROM_SIZE:
        raise SaveFormatError(
            "save must contain at least one 0x2000-byte EEPROM image"
        )
    physical_image = raw[:EEPROM_SIZE]
    wrapper = raw[EEPROM_SIZE:]
    image = SaveImage.parse(physical_image)
    tail = bytearray(image.tail)

    selected = select_newest(
        tail[A0 : A0 + SLOT_SIZE],
        tail[B0 : B0 + SLOT_SIZE],
    )
    selected_sequence = selected[1]
    next_sequence = (
        (selected_sequence + 1) & 0xFFFFFFFF
        if sequence is None
        else sequence & 0xFFFFFFFF
    )
    target = B0 if selected[0] == "A" else A0
    tail[target : target + SLOT_SIZE] = serialize_slot(
        sanitize(state),
        next_sequence,
    )

    updated_image = SaveImage(
        image.header,
        image.payload,
        bytes(tail),
    ).to_bytes()
    updated = updated_image + wrapper
    if physical_image[:TAIL_OFFSET] != updated_image[:TAIL_OFFSET]:
        raise SaveFormatError("internal error: bytes before tail changed")
    if wrapper != updated[EEPROM_SIZE:]:
        raise SaveFormatError("internal error: wrapper/padding bytes changed")
    output.write_bytes(updated)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--save", required=True)
    parser.add_argument("--output")
    parser.add_argument("--set-player-name")
    parser.add_argument("--set-bey-name")
    parser.add_argument("--avatar", type=int)
    parser.add_argument("--portrait", type=int)
    parser.add_argument("--origin", type=int)
    parser.add_argument("--tendency", type=int)
    parser.add_argument("--allow-unverified-tail-extension", action="store_true")
    arguments = parser.parse_args(argv)
    data = Path(arguments.save).read_bytes()
    report = extension_report(data)
    if not arguments.output:
        print(json.dumps(report, indent=2, sort_keys=True))
        return
    if not arguments.allow_unverified_tail_extension:
        parser.error(
            "editing requires --allow-unverified-tail-extension; use copied saves only"
        )
    print(WARNING, file=sys.stderr)
    state = CustomBladerState(**report["selected"]["state"])
    if arguments.set_player_name is not None:
        state.player_name = arguments.set_player_name
    if arguments.set_bey_name is not None:
        state.bey_name = arguments.set_bey_name
    if arguments.avatar is not None:
        state.avatar_id = arguments.avatar
    if arguments.portrait is not None:
        state.portrait_id = arguments.portrait
    if arguments.origin is not None:
        state.origin_id = arguments.origin
    if arguments.tendency is not None:
        state.tendency_id = arguments.tendency
    write_extension(
        Path(arguments.save),
        Path(arguments.output),
        sanitize(state),
        allow_unverified=True,
    )


if __name__ == "__main__":
    main()
