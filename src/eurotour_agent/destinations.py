from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from .history import destination_repeat_count
from .models import TripHistory, WatchFlags, WatchedTrip


@dataclass(frozen=True)
class DestinationSuggestion:
    city: str
    country: str
    score: float
    matched_tags: list[str]
    reasons: list[str]


@dataclass(frozen=True)
class DestinationProfile:
    city: str
    country: str
    tags: tuple[str, ...]
    music_strength: float
    rail_friendliness: float
    novelty: float


DESTINATION_CATALOG: tuple[DestinationProfile, ...] = (
    DestinationProfile("Lisbon", "Portugal", ("food", "walkable", "indie", "late-night", "coastal"), 0.74, 0.45, 0.85),
    DestinationProfile("Porto", "Portugal", ("food", "walkable", "galleries", "river", "value"), 0.55, 0.55, 0.83),
    DestinationProfile("Copenhagen", "Denmark", ("design", "electronic", "walkable", "food", "bike-friendly"), 0.75, 0.65, 0.78),
    DestinationProfile("Prague", "Czechia", ("value", "walkable", "architecture", "late-night", "rail-friendly"), 0.66, 0.72, 0.8),
    DestinationProfile("Vienna", "Austria", ("museums", "classical", "architecture", "rail-friendly", "food"), 0.58, 0.82, 0.76),
    DestinationProfile("Budapest", "Hungary", ("value", "late-night", "electronic", "thermal-baths", "walkable"), 0.77, 0.68, 0.82),
    DestinationProfile("Warsaw", "Poland", ("value", "museums", "electronic", "food", "architecture"), 0.68, 0.62, 0.86),
    DestinationProfile("Krakow", "Poland", ("value", "walkable", "food", "architecture", "late-night"), 0.57, 0.7, 0.84),
    DestinationProfile("Leipzig", "Germany", ("electronic", "galleries", "value", "rail-friendly", "walkable"), 0.72, 0.76, 0.88),
    DestinationProfile("Hamburg", "Germany", ("indie", "late-night", "waterfront", "rail-friendly", "food"), 0.7, 0.73, 0.74),
    DestinationProfile("Ghent", "Belgium", ("walkable", "rail-friendly", "food", "architecture", "value"), 0.52, 0.82, 0.83),
    DestinationProfile("Rotterdam", "Netherlands", ("design", "electronic", "architecture", "rail-friendly", "food"), 0.7, 0.86, 0.72),
    DestinationProfile("Lyon", "France", ("food", "walkable", "museums", "rail-friendly", "architecture"), 0.53, 0.78, 0.8),
    DestinationProfile("Bologna", "Italy", ("food", "walkable", "architecture", "rail-friendly", "value"), 0.54, 0.76, 0.82),
    DestinationProfile("Bilbao", "Spain", ("food", "galleries", "architecture", "coastal", "walkable"), 0.55, 0.5, 0.84),
    DestinationProfile("Valencia", "Spain", ("food", "coastal", "walkable", "architecture", "late-night"), 0.62, 0.52, 0.82),
)


def suggest_destinations(history: TripHistory | None, limit: int = 8) -> list[DestinationSuggestion]:
    preferred_tags = _preferred_tags(history)
    suggestions = [_score_destination(destination, preferred_tags, history) for destination in DESTINATION_CATALOG]
    return sorted(suggestions, key=lambda item: item.score, reverse=True)[:limit]


def draft_watched_trips(
    history: TripHistory | None,
    existing_destinations: set[str],
    earliest_start: date,
    latest_end: date,
    limit: int,
    budget_limit: float | None,
    nights_min: int = 3,
    nights_max: int = 5,
) -> list[WatchedTrip]:
    suggestions = suggest_destinations(history, limit=len(DESTINATION_CATALOG))
    drafted: list[WatchedTrip] = []
    normalized_existing = {destination.casefold() for destination in existing_destinations}
    for suggestion in suggestions:
        if suggestion.city.casefold() in normalized_existing:
            continue
        drafted.append(
            WatchedTrip(
                name=f"{suggestion.city} discovery scout",
                destination=suggestion.city,
                earliest_start=earliest_start,
                latest_end=latest_end,
                nights_min=nights_min,
                nights_max=nights_max,
                budget_limit=budget_limit,
                watch=WatchFlags(
                    flights=True,
                    trains=_profile_for_city(suggestion.city).rail_friendliness >= 0.65,
                    concerts=True,
                ),
                notes=_draft_notes(suggestion),
            )
        )
        if len(drafted) >= limit:
            break
    return drafted


def _score_destination(
    destination: DestinationProfile,
    preferred_tags: set[str],
    history: TripHistory | None,
) -> DestinationSuggestion:
    destination_tags = set(destination.tags)
    matched_tags = sorted(destination_tags & preferred_tags)
    repeat_count = destination_repeat_count(history, destination.city)
    tag_score = min(1.0, len(matched_tags) / 4)
    repeat_penalty = min(0.35, repeat_count * 0.18)
    score = (
        tag_score * 0.42
        + destination.music_strength * 0.22
        + destination.rail_friendliness * 0.16
        + destination.novelty * 0.2
        - repeat_penalty
    )
    reasons = _reasons(destination, matched_tags, repeat_count)
    return DestinationSuggestion(
        city=destination.city,
        country=destination.country,
        score=round(max(0.0, min(score, 1.0)), 3),
        matched_tags=matched_tags,
        reasons=reasons,
    )


def _profile_for_city(city: str) -> DestinationProfile:
    for destination in DESTINATION_CATALOG:
        if destination.city.casefold() == city.casefold():
            return destination
    raise KeyError(f"Unknown destination profile for {city!r}.")


def _draft_notes(suggestion: DestinationSuggestion) -> str:
    tags = ", ".join(suggestion.matched_tags) if suggestion.matched_tags else "new variety"
    return f"Suggested from trip history. Score {suggestion.score:.3f}; matched tags: {tags}."


def _preferred_tags(history: TripHistory | None) -> set[str]:
    if history is None:
        return set()
    preferred: set[str] = set()
    for trip in history.trips:
        if trip.rating is not None and trip.rating < 3.8:
            continue
        preferred.update(tag.casefold() for tag in trip.tags)
    return preferred


def _reasons(destination: DestinationProfile, matched_tags: list[str], repeat_count: int) -> list[str]:
    reasons = []
    if matched_tags:
        reasons.append("Matches prior liked tags: " + ", ".join(matched_tags) + ".")
    else:
        reasons.append("Adds destination variety outside the strongest prior tags.")
    if destination.music_strength >= 0.7:
        reasons.append("Strong baseline music-city signal for discovery.")
    if destination.rail_friendliness >= 0.75:
        reasons.append("Good rail and public-transport fit for Europe planning.")
    if repeat_count:
        reasons.append(f"Downranked because {destination.city} appears {repeat_count} time(s) in trip history.")
    return reasons
