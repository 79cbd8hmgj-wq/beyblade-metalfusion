"""Parse compact machine-readable GDB evidence emitted by Task 8 scripts."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

PREFIX = "TASK8|"


def _parse_value(key: str, value: str):
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if value.startswith(("0x", "0X")):
        return int(value, 16)
    if value.isdecimal():
        return int(value, 10)
    if key == "data":
        normalized = value.lower()
        if len(normalized) % 2 or any(ch not in "0123456789abcdef" for ch in normalized):
            raise ValueError("data must be even-length hexadecimal")
        return normalized
    return value


def parse_trace_lines(lines) -> list[dict]:
    events: list[dict] = []
    for raw_line in lines:
        line = raw_line.strip()
        if not line.startswith(PREFIX):
            continue
        event: dict = {}
        payload = line[len(PREFIX) :]
        if not payload:
            raise ValueError("TASK8 record has no fields")
        for item in payload.split("|"):
            if "=" not in item:
                raise ValueError("TASK8 fields must use key=value")
            key, value = item.split("=", 1)
            if not key or key in event:
                raise ValueError(f"duplicate or empty TASK8 key: {key!r}")
            event[key] = _parse_value(key, value)
        events.append(event)
    return events


def summarize_experiment(experiment: str, events: list[dict]) -> dict:
    selected = [event for event in events if event.get("experiment") == experiment]
    if not selected:
        return {
            "experiment": experiment,
            "status": "not_triggered",
            "confidence": "unknown",
            "event_count": 0,
            "events": [],
        }
    return {
        "experiment": experiment,
        "status": "executed",
        "confidence": "runtime_observed",
        "event_count": len(selected),
        "events": selected,
    }


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path)
    parser.add_argument("--experiment", action="append", default=[])
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args(argv)
    with arguments.trace.open(encoding="utf-8", errors="replace") as handle:
        events = parse_trace_lines(handle)
    experiments = arguments.experiment or sorted(
        {str(event["experiment"]) for event in events if "experiment" in event}
    )
    report = {
        "schema_version": 1,
        "source": str(arguments.trace),
        "experiments": [summarize_experiment(name, events) for name in experiments],
    }
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
