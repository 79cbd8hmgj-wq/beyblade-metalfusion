"""Canonical byte layout shared by Python tooling and future native code."""
from __future__ import annotations

import struct
from dataclasses import replace

from .custom_state import (
    MAX_NAME,
    CustomBladerState,
    compute_validation,
    is_valid,
    sanitize,
)

STATE_SIZE = 48
STATE_OFFSETS = {
    "schema_version": 0,
    "initialized": 1,
    "player_name": 2,
    "bey_name": 14,
    "avatar_id": 26,
    "portrait_id": 27,
    "skin_palette_id": 28,
    "hair_style_id": 29,
    "hair_palette_id": 30,
    "outfit_palette_id": 31,
    "origin_id": 32,
    "tendency_id": 33,
    "blank_core_state": 34,
    "blank_core_id": 35,
    "current_template_id": 36,
    "attack_ring_id": 37,
    "weight_disk_id": 38,
    "spin_gear_id": 39,
    "blade_base_id": 40,
    "future_flags": 41,
    "reserved": 42,
    "validation": 44,
}

_BYTE_FIELDS = (
    "avatar_id",
    "portrait_id",
    "skin_palette_id",
    "hair_style_id",
    "hair_palette_id",
    "outfit_palette_id",
    "origin_id",
    "tendency_id",
    "blank_core_state",
    "blank_core_id",
    "current_template_id",
    "attack_ring_id",
    "weight_disk_id",
    "spin_gear_id",
    "blade_base_id",
    "future_flags",
)


def _encode_name(value: str) -> bytes:
    encoded = value.encode("ascii", "strict")
    if not 1 <= len(encoded) <= MAX_NAME:
        raise ValueError("name length must be between 1 and 12 bytes")
    return encoded.ljust(MAX_NAME, b"\0")


def _decode_name(value: bytes) -> str:
    try:
        return value.split(b"\0", 1)[0].decode("ascii", "strict")
    except UnicodeDecodeError as exc:
        raise ValueError("invalid ASCII name") from exc


def serialize_state_bytes(state: CustomBladerState) -> bytes:
    state = sanitize(state)
    raw = bytearray(STATE_SIZE)
    raw[STATE_OFFSETS["schema_version"]] = state.schema_version
    raw[STATE_OFFSETS["initialized"]] = state.initialized & 0xFF
    raw[STATE_OFFSETS["player_name"] : STATE_OFFSETS["player_name"] + MAX_NAME] = _encode_name(state.player_name)
    raw[STATE_OFFSETS["bey_name"] : STATE_OFFSETS["bey_name"] + MAX_NAME] = _encode_name(state.bey_name)
    for field in _BYTE_FIELDS:
        raw[STATE_OFFSETS[field]] = getattr(state, field) & 0xFF
    raw[STATE_OFFSETS["reserved"] : STATE_OFFSETS["validation"]] = b"\0\0"
    struct.pack_into("<I", raw, STATE_OFFSETS["validation"], state.validation)
    return bytes(raw)


def parse_state_bytes(raw: bytes) -> CustomBladerState:
    if len(raw) != STATE_SIZE:
        raise ValueError("custom state must be exactly 48 bytes")
    if raw[STATE_OFFSETS["reserved"] : STATE_OFFSETS["validation"]] != b"\0\0":
        raise ValueError("reserved state bytes must be zero")

    values = {field: raw[STATE_OFFSETS[field]] for field in _BYTE_FIELDS}
    state = CustomBladerState(
        schema_version=raw[STATE_OFFSETS["schema_version"]],
        initialized=raw[STATE_OFFSETS["initialized"]],
        player_name=_decode_name(raw[STATE_OFFSETS["player_name"] : STATE_OFFSETS["player_name"] + MAX_NAME]),
        bey_name=_decode_name(raw[STATE_OFFSETS["bey_name"] : STATE_OFFSETS["bey_name"] + MAX_NAME]),
        validation=struct.unpack_from("<I", raw, STATE_OFFSETS["validation"])[0],
        **values,
    )
    if compute_validation(state) != state.validation:
        raise ValueError("custom state validation mismatch")
    if not is_valid(replace(state)):
        raise ValueError("custom state fields are invalid")
    return state
