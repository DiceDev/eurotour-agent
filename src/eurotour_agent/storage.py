from __future__ import annotations

import json
from pathlib import Path
from typing import TypeVar

import yaml
from pydantic import BaseModel

from .models import (
    AccommodationOption,
    CalendarSnapshot,
    CurrencyRateSnapshot,
    EventOption,
    ManualFindings,
    MusicTasteProfile,
    ResearchRun,
    TransportOption,
    TripHistory,
    Watchlist,
)

T = TypeVar("T", bound=BaseModel)


def load_watchlist(path: Path) -> Watchlist:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return Watchlist.model_validate(data)


def load_research_run(path: Path) -> ResearchRun:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    return ResearchRun.model_validate(data)


def load_manual_findings(path: Path) -> ManualFindings:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return ManualFindings.model_validate(data)


def load_calendar_snapshot(path: Path) -> CalendarSnapshot:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return CalendarSnapshot.model_validate(data)


def load_music_taste(path: Path) -> MusicTasteProfile:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return MusicTasteProfile.model_validate(data)


def load_currency_rates(path: Path) -> CurrencyRateSnapshot:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return CurrencyRateSnapshot.model_validate(data)


def load_trip_history(path: Path) -> TripHistory:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return TripHistory.model_validate(data)


def load_event_options(path: Path) -> list[EventOption]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    raw_events = data.get("event_options", data if isinstance(data, list) else [])
    return [EventOption.model_validate(item) for item in raw_events]


def load_transport_options(path: Path) -> list[TransportOption]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    raw_options = data.get("transport_options", data if isinstance(data, list) else [])
    return [TransportOption.model_validate(item) for item in raw_options]


def load_accommodation_options(path: Path) -> list[AccommodationOption]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    raw_options = data.get("accommodation_options", data if isinstance(data, list) else [])
    return [AccommodationOption.model_validate(item) for item in raw_options]


def write_yaml(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(data, handle, sort_keys=False, allow_unicode=False)


def write_model(path: Path, model: BaseModel) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        handle.write(model.model_dump_json(indent=2))
        handle.write("\n")
