from __future__ import annotations

from collections import Counter
from datetime import date

from .models import PastTrip, TripHistory


def destination_repeat_count(history: TripHistory | None, destination: str) -> int:
    return len(_matching_trips(history, destination))


def history_score_adjustment(history: TripHistory | None, destination: str, today: date | None = None) -> float:
    matches = _matching_trips(history, destination)
    if not matches:
        return 0.0

    affinity_bonus = _affinity_bonus(matches)
    repeat_penalty = _repeat_penalty(matches, today=today)
    return max(-0.08, min(0.06, affinity_bonus - repeat_penalty))


def history_reasons(history: TripHistory | None, destination: str) -> list[str]:
    matches = _matching_trips(history, destination)
    if not matches:
        return []

    ratings = [trip.rating for trip in matches if trip.rating is not None]
    reasons = [f"Trip history includes {len(matches)} prior visit(s) to {destination}."]
    if ratings:
        average = sum(ratings) / len(ratings)
        reasons.append(f"Average past rating for {destination} is {average:.1f}/5.")

    top_tags = _top_values(tag for trip in matches for tag in trip.tags)
    if top_tags:
        reasons.append("Past trip tags for this destination: " + ", ".join(top_tags) + ".")
    return reasons


def history_risks(history: TripHistory | None, destination: str, today: date | None = None) -> list[str]:
    matches = _matching_trips(history, destination)
    if not matches:
        return []

    risks: list[str] = []
    if len(matches) >= 2:
        risks.append("Destination has been repeated before; diversify unless there is a strong current event or fare reason.")
    if any(trip.would_repeat is False for trip in matches):
        risks.append("Past trip history includes a do-not-repeat signal for this destination.")
    if _repeat_penalty(matches, today=today) >= 0.06:
        risks.append("Recent or frequent prior visits reduce the diversity score.")
    return risks


def summarize_history(history: TripHistory) -> list[str]:
    if not history.trips:
        return ["No prior trips recorded."]

    destinations = Counter(_normalize(trip.destination) for trip in history.trips)
    tags = Counter(tag.casefold() for trip in history.trips for tag in trip.tags)
    ratings = [trip.rating for trip in history.trips if trip.rating is not None]
    lines = [f"Trips recorded: {len(history.trips)}"]
    lines.append("Destinations: " + ", ".join(f"{name}={count}" for name, count in sorted(destinations.items())))
    if tags:
        lines.append("Top tags: " + ", ".join(f"{tag}={count}" for tag, count in tags.most_common(8)))
    if ratings:
        lines.append(f"Average rating: {sum(ratings) / len(ratings):.1f}/5")
    recent = max(history.trips, key=lambda trip: trip.ended_on)
    lines.append(f"Most recent: {recent.destination} ending {recent.ended_on.isoformat()}")
    return lines


def _matching_trips(history: TripHistory | None, destination: str) -> list[PastTrip]:
    if history is None:
        return []
    normalized = _normalize(destination)
    return [trip for trip in history.trips if _normalize(trip.destination) == normalized]


def _affinity_bonus(matches: list[PastTrip]) -> float:
    ratings = [trip.rating for trip in matches if trip.rating is not None]
    if not ratings:
        base = 0.015 if any(trip.would_repeat for trip in matches) else 0.0
    else:
        average = sum(ratings) / len(ratings)
        base = max(0.0, (average - 3.5) / 1.5) * 0.04
    if any(trip.would_repeat for trip in matches):
        base += 0.015
    if any(trip.would_repeat is False for trip in matches):
        base -= 0.03
    return max(0.0, min(base, 0.06))


def _repeat_penalty(matches: list[PastTrip], today: date | None = None) -> float:
    penalty = max(0, len(matches) - 1) * 0.025
    latest = max(matches, key=lambda trip: trip.ended_on)
    today = today or date.today()
    days_since_latest = (today - latest.ended_on).days
    if 0 <= days_since_latest <= 365:
        penalty += 0.04
    elif 365 < days_since_latest <= 730:
        penalty += 0.02
    return max(0.0, min(penalty, 0.1))


def _top_values(values) -> list[str]:
    return [item for item, _ in Counter(value.casefold() for value in values).most_common(5)]


def _normalize(value: str) -> str:
    return value.strip().casefold()
