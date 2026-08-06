"""Sparse custom-state storage inside confirmed retail payload padding.

The retail serializer writes 83 records beginning at payload offset ``0x02E8``.
Each serialized record advances by ``0x0C`` bytes but writes only its first ten
bytes. The matching deserializer reads the same ten bytes and skips the final
two. Runtime multi-seed tracing confirmed that these two bytes remain untouched
in both serializer modes.

The first 32 padding pairs therefore provide exactly 64 bytes for the existing
``SU8C`` slot format. This module changes no bytes outside those positions.
The custom data remains covered by the retail payload checksum and transaction.
"""
from __future__ import annotations

from .custom_save import SLOT_SIZE, parse_slot, serialize_slot
from .custom_state import CustomBladerState, default_state

PAYLOAD_SIZE = 0x1F60
PADDING_TABLE_BASE = 0x02E8
PADDING_RECORD_COUNT = 83
PADDING_RECORD_STRIDE = 0x0C
PADDING_DATA_SIZE = 0x0A
PADDING_SIZE_PER_RECORD = 2
CUSTOM_SLOT_RECORDS = SLOT_SIZE // PADDING_SIZE_PER_RECORD

if CUSTOM_SLOT_RECORDS > PADDING_RECORD_COUNT:
    raise RuntimeError("custom slot exceeds confirmed retail padding records")


def _validate_payload(payload: bytes) -> None:
    if len(payload) != PAYLOAD_SIZE:
        raise ValueError(f"payload must be exactly 0x{PAYLOAD_SIZE:X} bytes")


def slot_offsets() -> tuple[int, ...]:
    """Return the 64 payload offsets used by the sparse custom slot."""
    return tuple(
        PADDING_TABLE_BASE
        + record_index * PADDING_RECORD_STRIDE
        + PADDING_DATA_SIZE
        + byte_index
        for record_index in range(CUSTOM_SLOT_RECORDS)
        for byte_index in range(PADDING_SIZE_PER_RECORD)
    )


def extract_slot(payload: bytes) -> bytes:
    """Gather the sparse payload bytes into one contiguous 64-byte slot."""
    _validate_payload(payload)
    return bytes(payload[offset] for offset in slot_offsets())


def embed_slot(payload: bytes, slot: bytes) -> bytes:
    """Return a payload copy with only the mapped padding bytes replaced."""
    _validate_payload(payload)
    if len(slot) != SLOT_SIZE:
        raise ValueError(f"slot must be exactly {SLOT_SIZE} bytes")
    output = bytearray(payload)
    for offset, value in zip(slot_offsets(), slot):
        output[offset] = value
    return bytes(output)


def load_state(payload: bytes) -> tuple[CustomBladerState, int, str]:
    """Load a valid custom slot or return the canonical default state."""
    valid, sequence, state, status = parse_slot(extract_slot(payload))
    if not valid or state is None:
        return default_state(), 0, f"default: {status}"
    return state, sequence, status


def embed_state(
    payload: bytes,
    state: CustomBladerState,
    *,
    sequence: int,
) -> bytes:
    """Serialize and embed one custom state using the established slot format."""
    return embed_slot(payload, serialize_slot(state, sequence))
