"""64-byte transaction slot model for the Task 8 custom save extension."""
from __future__ import annotations

import binascii
import struct
from dataclasses import replace

from .custom_state import (
    MAX_NAME,
    SCHEMA_VERSION,
    CustomBladerState,
    compute_validation,
    default_state,
    sanitize,
)

SLOT_SIZE = 64
BLOCK_SIZE = 8
SLOT_BLOCK_COUNT = SLOT_SIZE // BLOCK_SIZE
SLOT_A_BLOCKS = (0x3EF, 0x3F6)
SLOT_B_BLOCKS = (0x3F7, 0x3FE)
RESERVED_BLOCK = 0x3FF
MAGIC = b"SU8C"
COMMIT = b"OK8!"


def _enc(value: str) -> bytes:
    return value.encode("ascii", "strict")[:MAX_NAME].ljust(MAX_NAME, b"\0")


def _dec(value: bytes) -> str:
    try:
        return value.split(b"\0", 1)[0].decode("ascii", "strict")
    except UnicodeDecodeError as exc:
        raise ValueError("invalid ASCII name") from exc


def crc(data: bytes) -> int:
    return binascii.crc32(data) & 0xFFFFFFFF


def serialize_slot(state: CustomBladerState, sequence: int) -> bytes:
    state = sanitize(state)
    body = bytearray(56)
    body[0:4] = MAGIC
    struct.pack_into("<I", body, 4, sequence & 0xFFFFFFFF)
    body[8] = SCHEMA_VERSION
    body[9] = state.initialized & 0xFF
    body[10:22] = _enc(state.player_name)
    body[22:34] = _enc(state.bey_name)
    body[34:46] = bytes(
        [
            state.avatar_id,
            state.portrait_id,
            state.skin_palette_id,
            state.hair_style_id,
            state.hair_palette_id,
            state.outfit_palette_id,
            state.origin_id,
            state.tendency_id,
            state.blank_core_state,
            state.blank_core_id,
            state.current_template_id,
            state.future_flags,
        ]
    )
    body[46:50] = struct.pack(
        "<BBBB",
        state.attack_ring_id,
        state.weight_disk_id,
        state.spin_gear_id,
        state.blade_base_id,
    )
    body[50:54] = struct.pack("<I", state.validation)
    tail = struct.pack("<I4s", crc(bytes(body)), COMMIT)
    return bytes(body) + tail


def parse_slot(raw: bytes) -> tuple[bool, int, CustomBladerState | None, str]:
    if len(raw) != SLOT_SIZE:
        return False, 0, None, "slot must be 64 bytes"
    if raw[0:4] != MAGIC:
        return False, 0, None, "missing magic"
    if raw[60:64] != COMMIT:
        return False, 0, None, "missing commit"
    got = struct.unpack_from("<I", raw, 56)[0]
    if got != crc(raw[:56]):
        return False, 0, None, "crc mismatch"
    if raw[8] > SCHEMA_VERSION:
        return False, 0, None, "newer schema"

    sequence = struct.unpack_from("<I", raw, 4)[0]
    fields = list(raw[34:46])
    components = list(raw[46:50])
    validation = struct.unpack_from("<I", raw, 50)[0]
    try:
        state = CustomBladerState(
            schema_version=raw[8],
            initialized=raw[9],
            player_name=_dec(raw[10:22]),
            bey_name=_dec(raw[22:34]),
            avatar_id=fields[0],
            portrait_id=fields[1],
            skin_palette_id=fields[2],
            hair_style_id=fields[3],
            hair_palette_id=fields[4],
            outfit_palette_id=fields[5],
            origin_id=fields[6],
            tendency_id=fields[7],
            blank_core_state=fields[8],
            blank_core_id=fields[9],
            current_template_id=fields[10],
            future_flags=fields[11],
            attack_ring_id=components[0],
            weight_disk_id=components[1],
            spin_gear_id=components[2],
            blade_base_id=components[3],
            validation=validation,
        )
    except ValueError as exc:
        return False, 0, None, str(exc)

    if compute_validation(state) != validation:
        return False, 0, None, "state validation mismatch"

    normalized = sanitize(replace(state))
    if normalized.to_dict() != state.to_dict():
        return False, 0, None, "invalid state fields"
    return True, sequence, state, "valid"


def seq_newer(a: int, b: int) -> bool:
    difference = (a - b) & 0xFFFFFFFF
    return 0 < difference < 0x80000000


def select_newest(slot_a: bytes, slot_b: bytes):
    valid_a, sequence_a, state_a, _ = parse_slot(slot_a)
    valid_b, sequence_b, state_b, _ = parse_slot(slot_b)
    if valid_a and valid_b:
        if seq_newer(sequence_a, sequence_b):
            return "A", sequence_a, state_a
        if seq_newer(sequence_b, sequence_a):
            return "B", sequence_b, state_b
        # Equal or exactly half-range-apart sequences are ambiguous. Prefer A
        # deterministically instead of allowing slot order to vary by caller.
        return "A", sequence_a, state_a
    if valid_a:
        return "A", sequence_a, state_a
    if valid_b:
        return "B", sequence_b, state_b
    return "default", 0, default_state()


def simulate_slot_transaction(
    slot_a: bytes,
    slot_b: bytes,
    state: CustomBladerState,
    *,
    interrupt_after_block: int | None,
) -> tuple[bytes, bytes]:
    """Model data-first, commit-last writes to the inactive 64-byte slot.

    ``interrupt_after_block`` is the number of complete eight-byte blocks that
    reached EEPROM before power loss. ``None`` writes all eight blocks.
    """
    if len(slot_a) != SLOT_SIZE or len(slot_b) != SLOT_SIZE:
        raise ValueError("both slots must be 64 bytes")
    if interrupt_after_block is not None and not 0 <= interrupt_after_block <= SLOT_BLOCK_COUNT:
        raise ValueError("interrupt_after_block must be between 0 and 8")

    selected_slot, selected_sequence, _ = select_newest(slot_a, slot_b)
    target_slot = "B" if selected_slot == "A" else "A"
    next_sequence = (selected_sequence + 1) & 0xFFFFFFFF
    encoded = serialize_slot(state, next_sequence)
    blocks_to_write = SLOT_BLOCK_COUNT if interrupt_after_block is None else interrupt_after_block

    next_a = bytearray(slot_a)
    next_b = bytearray(slot_b)
    target = next_b if target_slot == "B" else next_a
    for block_index in range(blocks_to_write):
        start = block_index * BLOCK_SIZE
        target[start : start + BLOCK_SIZE] = encoded[start : start + BLOCK_SIZE]
    return bytes(next_a), bytes(next_b)
