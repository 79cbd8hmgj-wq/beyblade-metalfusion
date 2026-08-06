"""Instruction-oriented SU8C validation model for the native Task 8 module.

The GBA runtime stores one raw 64-byte ``SU8C`` slot at the end of the expanded
root allocation. This module defines the exact checks and hashes the Thumb
implementation must reproduce before creator UI is allowed to edit the state.
"""
from __future__ import annotations

import binascii
import struct

from .custom_save import COMMIT, MAGIC, SLOT_SIZE, serialize_slot
from .custom_state import (
    BLANK_CORE_DORMANT,
    BLANK_CORE_ID,
    SCHEMA_VERSION,
    default_state,
)

STATE_HASH_SEED = 0x43555354
NAME_RANGES = ((10, 22), (22, 34))
ID_OFFSETS = (34, 35, 36, 38, 39, 40, 41)
STATE_NUMERIC_ORDER = (
    34,
    35,
    36,
    37,
    38,
    39,
    40,
    41,
    42,
    43,
    44,
    46,
    47,
    48,
    49,
    45,
)
ALLOWED_NAME_BYTES = frozenset(
    b" ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'-"
)


def _require_slot(raw: bytes) -> None:
    if len(raw) != SLOT_SIZE:
        raise ValueError("slot must be exactly 64 bytes")


def _hash_step(value: int, byte: int) -> int:
    return ((value << 5) - value + byte) & 0xFFFFFFFF


def _name_bytes(raw: bytes, start: int, end: int) -> bytes:
    field = raw[start:end]
    terminator = field.find(b"\0")
    return field if terminator < 0 else field[:terminator]


def _valid_name(raw: bytes, start: int, end: int) -> bool:
    value = _name_bytes(raw, start, end)
    if not value or value[0] == 0x20 or value[-1] == 0x20:
        return False
    return all(byte in ALLOWED_NAME_BYTES for byte in value)


def state_validation(raw: bytes) -> int:
    """Compute the dataclass-order validation word from one raw slot."""
    _require_slot(raw)
    value = STATE_HASH_SEED
    value = _hash_step(value, raw[8])
    value = _hash_step(value, raw[9])
    for start, end in NAME_RANGES:
        for byte in _name_bytes(raw, start, end):
            value = _hash_step(value, byte)
    for offset in STATE_NUMERIC_ORDER:
        value = _hash_step(value, raw[offset])
    return value


def _field_invariants_valid(raw: bytes) -> bool:
    if raw[8] != SCHEMA_VERSION:
        return False
    if not all(_valid_name(raw, start, end) for start, end in NAME_RANGES):
        return False
    if any(raw[offset] > 3 for offset in ID_OFFSETS):
        return False
    if raw[37] != raw[34] or raw[37] > 3:
        return False
    if raw[42] != BLANK_CORE_DORMANT or raw[43] != BLANK_CORE_ID:
        return False
    if raw[54:56] != b"\0\0":
        return False
    return True


def validate_slot(raw: bytes) -> bool:
    """Return whether a raw runtime slot is safe to activate."""
    if len(raw) != SLOT_SIZE:
        return False
    if raw[0:4] != MAGIC or raw[60:64] != COMMIT:
        return False
    if not _field_invariants_valid(raw):
        return False
    if struct.unpack_from("<I", raw, 50)[0] != state_validation(raw):
        return False
    expected_crc = binascii.crc32(raw[:56]) & 0xFFFFFFFF
    if struct.unpack_from("<I", raw, 56)[0] != expected_crc:
        return False
    return True


def seal_slot(raw: bytes) -> bytes:
    """Restore fixed fields and recompute both integrity layers.

    Creator code controls the editable fields. This function deliberately
    refuses invalid names and customization IDs rather than silently converting
    arbitrary memory into a valid save state.
    """
    _require_slot(raw)
    output = bytearray(raw)
    output[0:4] = MAGIC
    output[8] = SCHEMA_VERSION
    output[37] = output[34]
    output[42] = BLANK_CORE_DORMANT
    output[43] = BLANK_CORE_ID
    output[54:56] = b"\0\0"
    output[60:64] = COMMIT
    if not _field_invariants_valid(output):
        raise ValueError("slot fields are not valid for native sealing")
    struct.pack_into("<I", output, 50, state_validation(output))
    struct.pack_into(
        "<I",
        output,
        56,
        binascii.crc32(output[:56]) & 0xFFFFFFFF,
    )
    return bytes(output)


def default_slot() -> bytes:
    """Return the deterministic sequence-zero default runtime slot."""
    return serialize_slot(default_state(), 0)


def validate_or_default(raw: bytes) -> tuple[bytes, str]:
    """Preserve a valid slot or replace it with the canonical default."""
    _require_slot(raw)
    if validate_slot(raw):
        return bytes(raw), "valid"
    return default_slot(), "defaulted"


def commit_player_name(raw: bytes, retail_buffer: bytes) -> tuple[bytes, str]:
    """Copy the retail 16-byte keyboard buffer into the persistent name field.

    The retail scene accepts up to 15 characters, while the SU8C ABI reserves
    12 bytes. The native hook therefore copies the first 12 bytes exactly and
    reseals the slot. A name that violates the native field invariants defaults
    the whole slot rather than activating corrupt state.
    """
    _require_slot(raw)
    if len(retail_buffer) != 16:
        raise ValueError("retail name buffer must be exactly 16 bytes")
    output = bytearray(raw)
    output[10:22] = retail_buffer[:12]
    try:
        return seal_slot(bytes(output)), "committed"
    except ValueError:
        return default_slot(), "defaulted"
