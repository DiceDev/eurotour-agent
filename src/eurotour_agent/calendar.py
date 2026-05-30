from __future__ import annotations

from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from .models import BusyCalendarEvent, CalendarSnapshot, CalendarWindow


def find_free_windows(
    snapshot: CalendarSnapshot,
    min_nights: int,
    max_nights: int | None = None,
    buffer_hours: float = 2.0,
) -> list[CalendarWindow]:
    if min_nights < 1:
        raise ValueError("min_nights must be at least 1")
    if max_nights is not None and max_nights < min_nights:
        raise ValueError("max_nights must be greater than or equal to min_nights")

    tz = ZoneInfo(snapshot.timezone)
    range_start = snapshot.range_start.astimezone(tz)
    range_end = snapshot.range_end.astimezone(tz)
    busy_events = _normalized_busy_events(snapshot.busy_events, tz, buffer_hours)
    free_windows: list[CalendarWindow] = []
    cursor = range_start

    for event in busy_events:
        if event.starts_at > cursor:
            maybe_window = _build_window(cursor, event.starts_at, min_nights, max_nights)
            if maybe_window:
                free_windows.append(maybe_window)
        cursor = max(cursor, event.ends_at)

    if cursor < range_end:
        maybe_window = _build_window(cursor, range_end, min_nights, max_nights)
        if maybe_window:
            free_windows.append(maybe_window)

    return free_windows


def _normalized_busy_events(
    busy_events: list[BusyCalendarEvent],
    tz: ZoneInfo,
    buffer_hours: float,
) -> list[BusyCalendarEvent]:
    buffer = timedelta(hours=buffer_hours)
    blocking = [
        BusyCalendarEvent(
            starts_at=event.starts_at.astimezone(tz) - buffer,
            ends_at=event.ends_at.astimezone(tz) + buffer,
            title=event.title,
            source=event.source,
            transparent=event.transparent,
        )
        for event in busy_events
        if not event.transparent
    ]
    blocking.sort(key=lambda item: item.starts_at)

    merged: list[BusyCalendarEvent] = []
    for event in blocking:
        if not merged or event.starts_at > merged[-1].ends_at:
            merged.append(event)
            continue
        merged[-1] = BusyCalendarEvent(
            starts_at=merged[-1].starts_at,
            ends_at=max(merged[-1].ends_at, event.ends_at),
            title=merged[-1].title,
            source=merged[-1].source,
        )
    return merged


def _build_window(
    starts_at: datetime,
    ends_at: datetime,
    min_nights: int,
    max_nights: int | None,
) -> CalendarWindow | None:
    starts_at = _next_day_start(starts_at)
    ends_at = _previous_day_end(ends_at)
    if ends_at <= starts_at:
        return None

    nights = (ends_at.date() - starts_at.date()).days
    if nights < min_nights:
        return None

    if max_nights is not None and nights > max_nights:
        ends_at = starts_at + timedelta(days=max_nights)

    return CalendarWindow(
        starts_at=starts_at,
        ends_at=ends_at,
        label=f"Free for {min(nights, max_nights or nights)} night(s)",
    )


def _next_day_start(value: datetime) -> datetime:
    if value.time() <= time(hour=6):
        return value.replace(hour=0, minute=0, second=0, microsecond=0)
    next_day = value.date() + timedelta(days=1)
    return datetime.combine(next_day, time.min, tzinfo=value.tzinfo)


def _previous_day_end(value: datetime) -> datetime:
    if value.time() >= time(hour=18):
        return value.replace(hour=23, minute=59, second=0, microsecond=0)
    previous_day = value.date() - timedelta(days=1)
    return datetime.combine(previous_day, time(hour=23, minute=59), tzinfo=value.tzinfo)
