"""Analyze byte preservation across retail save serializer experiments.

Runtime experiments seed the entire 0x1F60-byte payload, invoke the serializer,
and dump the result. This tool intersects bytes that remain identical across
multiple seeds and serializer modes so one coincidental value cannot be treated
as unused storage.

Example manifest::

    {
      "runs": [
        {"seed": "0xA5", "mode": 0,
         "before": "runtime/seed-a5.bin", "after": "runtime/mode0-a5.bin"}
      ]
    }

Paths are resolved relative to the manifest. Full payload dumps belong in an
ignored runtime directory; compact reports may be tracked.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable, Sequence

from src.custom_blader.payload_storage import (
    CUSTOM_SLOT_RECORDS,
    PADDING_DATA_SIZE,
    PADDING_RECORD_COUNT,
    PADDING_RECORD_STRIDE,
    PADDING_SIZE_PER_RECORD,
    PADDING_TABLE_BASE,
    PAYLOAD_SIZE,
    slot_offsets,
)

SERIALIZER = 0x08045198
DESERIALIZER = 0x08045590


def unchanged_offsets(before: bytes, after: bytes) -> set[int]:
    if len(before) != len(after):
        raise ValueError("before and after payloads must have the same length")
    if len(before) != PAYLOAD_SIZE:
        raise ValueError(f"payload runs must be exactly 0x{PAYLOAD_SIZE:X} bytes")
    return {index for index, pair in enumerate(zip(before, after)) if pair[0] == pair[1]}


def intersect_unchanged_offsets(runs: Sequence[tuple[bytes, bytes]]) -> set[int]:
    if not runs:
        raise ValueError("at least one serializer run is required")
    intersection: set[int] | None = None
    for before, after in runs:
        current = unchanged_offsets(before, after)
        intersection = current if intersection is None else intersection & current
    return intersection if intersection is not None else set()


def coalesce_offsets(offsets: Iterable[int]) -> list[dict[str, int]]:
    ordered = sorted(set(offsets))
    if not ordered:
        return []
    ranges: list[dict[str, int]] = []
    start = previous = ordered[0]
    for offset in ordered[1:]:
        if offset == previous + 1:
            previous = offset
            continue
        ranges.append(
            {
                "start": start,
                "end_exclusive": previous + 1,
                "size": previous + 1 - start,
            }
        )
        start = previous = offset
    ranges.append(
        {
            "start": start,
            "end_exclusive": previous + 1,
            "size": previous + 1 - start,
        }
    )
    return ranges


def record_padding_offsets(record_count: int = PADDING_RECORD_COUNT) -> tuple[int, ...]:
    if not 0 <= record_count <= PADDING_RECORD_COUNT:
        raise ValueError(f"record_count must be between 0 and {PADDING_RECORD_COUNT}")
    return tuple(
        PADDING_TABLE_BASE
        + record_index * PADDING_RECORD_STRIDE
        + PADDING_DATA_SIZE
        + byte_index
        for record_index in range(record_count)
        for byte_index in range(PADDING_SIZE_PER_RECORD)
    )


def confirmed_untouched_offsets() -> set[int]:
    """Return the multi-seed, both-mode runtime-confirmed intersection."""
    offsets = set(range(0x0000, 0x0004))
    offsets.update(range(0x0054, 0x0058))
    offsets.add(0x02E7)
    offsets.update(record_padding_offsets())
    offsets.add(0x1F5F)
    if len(offsets) != 176:
        raise RuntimeError("confirmed preservation set changed unexpectedly")
    return offsets


def _hex_range(item: dict[str, int]) -> dict[str, int | str]:
    return {
        "start": f"0x{item['start']:04X}",
        "end_exclusive": f"0x{item['end_exclusive']:04X}",
        "size": item["size"],
    }


def confirmed_runtime_report() -> dict:
    untouched = confirmed_untouched_offsets()
    custom_offsets = slot_offsets()
    return {
        "schema_version": 1,
        "evidence_kind": "runtime_multi_seed_serializer_intersection",
        "serializer": f"0x{SERIALIZER:08X}",
        "deserializer": f"0x{DESERIALIZER:08X}",
        "payload_size": f"0x{PAYLOAD_SIZE:04X}",
        "serializer_modes_tested": [0, 1],
        "seed_values_tested": ["0xA5", "0x5A", "0x3C"],
        "preserved_byte_count": len(untouched),
        "preserved_ranges": [_hex_range(item) for item in coalesce_offsets(untouched)],
        "isolated_holes": [
            {"start": "0x0000", "end_exclusive": "0x0004", "role": "checksum_word_written_by_caller"},
            {"start": "0x0054", "end_exclusive": "0x0058", "role": "serializer_untouched_hole"},
            {"start": "0x02E7", "end_exclusive": "0x02E8", "role": "alignment_gap"},
            {"start": "0x1F5F", "end_exclusive": "0x1F60", "role": "trailing_byte"},
        ],
        "record_table": {
            "base": f"0x{PADDING_TABLE_BASE:04X}",
            "count": PADDING_RECORD_COUNT,
            "stride": f"0x{PADDING_RECORD_STRIDE:02X}",
            "serialized_bytes_per_record": PADDING_DATA_SIZE,
            "padding_bytes_per_record": PADDING_SIZE_PER_RECORD,
            "first_padding": "0x02F2-0x02F3",
            "last_padding": "0x06CA-0x06CB",
            "serializer_loop": "0x08045412-0x080454A0",
            "deserializer_loop": "0x08045844-0x08045954",
        },
        "custom_slot": {
            "format": "SU8C",
            "record_count": CUSTOM_SLOT_RECORDS,
            "size": len(custom_offsets),
            "first_payload_offset": f"0x{custom_offsets[0]:04X}",
            "last_payload_offset": f"0x{custom_offsets[-1]:04X}",
            "mapping": "slot[2*i:2*i+2] <-> payload[0x02E8 + i*0x0C + 0x0A : +0x0C], i=0..31",
            "covered_by_retail_checksum": True,
            "covered_by_retail_transaction": True,
        },
        "eeprom_tail_required": False,
        "confidence": "confirmed",
        "scope_limit": "The experiment proves serializer/deserializer preservation. It does not by itself prove that no unrelated high-level routine accesses the RAM payload padding directly.",
    }


def report_from_runs(runs: Sequence[tuple[bytes, bytes]], metadata: list[dict] | None = None) -> dict:
    offsets = intersect_unchanged_offsets(runs)
    report = confirmed_runtime_report()
    report.update(
        {
            "run_count": len(runs),
            "run_metadata": metadata or [],
            "observed_preserved_byte_count": len(offsets),
            "observed_preserved_ranges": [_hex_range(item) for item in coalesce_offsets(offsets)],
            "confirmed_set_matches": offsets == confirmed_untouched_offsets(),
        }
    )
    return report


def load_manifest(path: Path) -> tuple[list[tuple[bytes, bytes]], list[dict]]:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    rows = manifest.get("runs")
    if not isinstance(rows, list) or not rows:
        raise ValueError("manifest must contain a non-empty runs array")
    runs: list[tuple[bytes, bytes]] = []
    metadata: list[dict] = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict) or "before" not in row or "after" not in row:
            raise ValueError(f"run {index} requires before and after paths")
        before_path = (path.parent / row["before"]).resolve()
        after_path = (path.parent / row["after"]).resolve()
        runs.append((before_path.read_bytes(), after_path.read_bytes()))
        metadata.append({key: value for key, value in row.items() if key not in {"before", "after"}})
    return runs, metadata


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, help="JSON manifest containing runtime payload pairs")
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args(argv)
    if arguments.manifest:
        runs, metadata = load_manifest(arguments.manifest)
        report = report_from_runs(runs, metadata)
    else:
        report = confirmed_runtime_report()
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
