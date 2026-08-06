from __future__ import annotations

import json
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

from .custom_state import CustomBladerState, default_state, sanitize

STEPS = (
    "player_name",
    "bey_name",
    "avatar",
    "skin",
    "hair",
    "outfit",
    "portrait",
    "origin",
    "tendency",
    "summary",
    "confirm",
)

OPTION_CATEGORIES = (
    "avatars",
    "skin_palettes",
    "hair_palettes",
    "outfit_palettes",
    "portraits",
    "origins",
    "tendencies",
)

STEP_SELECTIONS = {
    "avatar": ("avatar_id", "avatars"),
    "skin": ("skin_palette_id", "skin_palettes"),
    "hair": ("hair_palette_id", "hair_palettes"),
    "outfit": ("outfit_palette_id", "outfit_palettes"),
    "portrait": ("portrait_id", "portraits"),
    "origin": ("origin_id", "origins"),
    "tendency": ("tendency_id", "tendencies"),
}

PERSISTED_FIELDS = frozenset(CustomBladerState.__dataclass_fields__)


def _default_options_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "data"
        / "custom_blader"
        / "creator-options.json"
    )


def load_creator_options(path: str | Path | None = None) -> dict[str, Any]:
    source = Path(path) if path is not None else _default_options_path()
    data = json.loads(source.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1:
        raise ValueError("unsupported creator option schema")
    defaults = data.get("defaults")
    if not isinstance(defaults, dict):
        raise ValueError("creator option defaults are missing")
    for category in OPTION_CATEGORIES:
        entries = data.get(category)
        if not isinstance(entries, list) or not entries:
            raise ValueError(f"creator option category is missing: {category}")
        ids = [entry.get("id") for entry in entries]
        if ids != list(range(len(entries))):
            raise ValueError(f"creator option IDs must be contiguous: {category}")
        if any(
            not isinstance(entry.get("label"), str) or not entry["label"]
            for entry in entries
        ):
            raise ValueError(f"creator option label is missing: {category}")
        if defaults.get(category) not in ids:
            raise ValueError(f"creator option default is invalid: {category}")
    return data


def _label(options: dict[str, Any], category: str, value: int) -> str:
    for entry in options[category]:
        if entry["id"] == value:
            return entry["label"]
    default_id = options["defaults"][category]
    return next(
        entry["label"]
        for entry in options[category]
        if entry["id"] == default_id
    )


@dataclass
class CreatorModel:
    index: int = 0
    state: CustomBladerState | None = None
    cancelled: bool = False
    completed: bool = False
    existing_save: bool = False
    options: dict[str, Any] | None = field(default=None, repr=False)
    bypassed: bool = field(init=False)

    def __post_init__(self) -> None:
        self.options = (
            load_creator_options() if self.options is None else self.options
        )
        self.state = (
            default_state()
            if self.state is None
            else sanitize(replace(self.state))
        )
        self.index = max(0, min(int(self.index), len(STEPS) - 1))
        self.bypassed = bool(self.existing_save)

    @property
    def active(self) -> bool:
        return not self.cancelled and not self.completed and not self.bypassed

    @property
    def step(self) -> str:
        if self.completed or self.bypassed:
            return "complete"
        if self.cancelled:
            return "cancelled"
        return STEPS[self.index]

    def next(self) -> "CreatorModel":
        if self.active:
            self.index = min(self.index + 1, len(STEPS) - 1)
        return self

    def back(self) -> "CreatorModel":
        if self.active:
            self.index = max(self.index - 1, 0)
        return self

    def cancel(self) -> "CreatorModel":
        if self.active:
            self.cancelled = True
        return self

    def restart(self) -> "CreatorModel":
        self.index = 0
        self.state = default_state()
        self.cancelled = False
        self.completed = False
        self.bypassed = bool(self.existing_save)
        return self

    def choose(self, field_name: str, value: Any) -> "CreatorModel":
        if not self.active:
            return self
        if field_name not in PERSISTED_FIELDS or field_name in {
            "schema_version",
            "validation",
            "blank_core_state",
            "blank_core_id",
        }:
            raise ValueError(f"unsupported creator field: {field_name}")
        setattr(self.state, field_name, value)
        sanitize(self.state)
        return self

    def select(self, value: Any) -> "CreatorModel":
        if not self.active:
            return self
        if self.step == "player_name":
            return self.choose("player_name", value)
        if self.step == "bey_name":
            return self.choose("bey_name", value)
        if self.step not in STEP_SELECTIONS:
            raise RuntimeError("current creator step does not accept a selection")
        field_name, category = STEP_SELECTIONS[self.step]
        ids = {entry["id"] for entry in self.options[category]}
        selected = (
            int(value)
            if int(value) in ids
            else self.options["defaults"][category]
        )
        return self.choose(field_name, selected)

    def summary(self) -> dict[str, Any]:
        return {
            "player_name": self.state.player_name,
            "bey_name": self.state.bey_name,
            "avatar": _label(self.options, "avatars", self.state.avatar_id),
            "skin": _label(
                self.options,
                "skin_palettes",
                self.state.skin_palette_id,
            ),
            "hair": _label(
                self.options,
                "hair_palettes",
                self.state.hair_palette_id,
            ),
            "outfit": _label(
                self.options,
                "outfit_palettes",
                self.state.outfit_palette_id,
            ),
            "portrait": _label(
                self.options,
                "portraits",
                self.state.portrait_id,
            ),
            "origin": _label(self.options, "origins", self.state.origin_id),
            "tendency": _label(
                self.options,
                "tendencies",
                self.state.tendency_id,
            ),
        }

    def confirm(self) -> CustomBladerState:
        if not self.active or self.step != "confirm":
            raise RuntimeError("creator must be on the confirm step")
        self.state = sanitize(replace(self.state))
        self.completed = True
        return replace(self.state)
