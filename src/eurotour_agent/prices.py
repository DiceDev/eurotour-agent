from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime

from .models import CandidateTrip, CostCategory, PriceAlert, PriceHistory, PriceObservation, ResearchRun


def price_alerts(history: PriceHistory, drop_threshold_percent: float = 10.0) -> list[PriceAlert]:
    grouped: dict[tuple[str, str, str, str], list[PriceObservation]] = defaultdict(list)
    for observation in history.observations:
        key = (
            observation.watched_trip.casefold(),
            observation.category.value,
            observation.label.casefold(),
            observation.currency,
        )
        grouped[key].append(observation)

    alerts: list[PriceAlert] = []
    for observations in grouped.values():
        ordered = sorted(observations, key=lambda item: item.observed_at)
        if len(ordered) < 2:
            continue
        current = ordered[-1]
        previous = ordered[:-1]
        previous_low = min(item.amount for item in previous)
        previous_latest = previous[-1].amount
        drop_percent = _drop_percent(previous_latest, current.amount)
        is_new_low = current.amount < previous_low
        if not is_new_low and (drop_percent is None or drop_percent < drop_threshold_percent):
            continue
        alerts.append(
            PriceAlert(
                watched_trip=current.watched_trip,
                category=current.category,
                label=current.label,
                current_amount=current.amount,
                previous_low_amount=previous_low,
                currency=current.currency,
                drop_percent=drop_percent,
                is_new_low=is_new_low,
                observed_at=current.observed_at,
                source=current.source,
                url=current.url,
                reason=_alert_reason(current, previous_low, drop_percent, is_new_low, drop_threshold_percent),
            )
        )
    return sorted(alerts, key=lambda item: (not item.is_new_low, -(item.drop_percent or 0), item.watched_trip))


def observations_from_research_run(research_run: ResearchRun) -> list[PriceObservation]:
    observations: list[PriceObservation] = []
    observed_at = research_run.generated_at or datetime.now(UTC)
    for trip in research_run.candidate_trips:
        observations.extend(_transport_observations(trip, observed_at))
        observations.extend(_accommodation_observations(trip, observed_at))
        observations.extend(_event_observations(trip, observed_at))
        for component in trip.cost_components:
            if component.amount is None:
                continue
            observations.append(
                PriceObservation(
                    watched_trip=trip.name,
                    category=component.category,
                    label=component.label,
                    source=component.source,
                    amount=component.amount,
                    currency=component.currency,
                    observed_at=observed_at,
                    notes=component.notes,
                )
            )
    return observations


def append_observations(history: PriceHistory, observations: list[PriceObservation]) -> PriceHistory:
    existing_keys = {_observation_key(observation) for observation in history.observations}
    merged = list(history.observations)
    for observation in observations:
        key = _observation_key(observation)
        if key in existing_keys:
            continue
        existing_keys.add(key)
        merged.append(observation)
    return PriceHistory(observations=sorted(merged, key=lambda item: item.observed_at))


def _drop_percent(previous_amount: float, current_amount: float) -> float | None:
    if previous_amount <= 0:
        return None
    return round(max(0.0, (previous_amount - current_amount) / previous_amount * 100), 1)


def _alert_reason(
    current: PriceObservation,
    previous_low: float,
    drop_percent: float | None,
    is_new_low: bool,
    threshold: float,
) -> str:
    if is_new_low and drop_percent is not None and drop_percent >= threshold:
        return f"New tracked low and {drop_percent:.1f}% below the previous observation."
    if is_new_low:
        return f"New tracked low below prior low {previous_low:.2f} {current.currency}."
    return f"Price dropped {drop_percent:.1f}% from the previous observation."


def _transport_observations(trip: CandidateTrip, observed_at: datetime) -> list[PriceObservation]:
    observations = []
    for option in trip.transport_options:
        if option.price_amount is None:
            continue
        observations.append(
            PriceObservation(
                watched_trip=trip.name,
                category=CostCategory.TRANSPORT,
                label=f"{option.mode}: {option.origin} to {option.destination}",
                source=option.source,
                amount=option.price_amount,
                currency=option.price_currency,
                observed_at=option.observed_at or observed_at,
                url=option.booking_url,
                notes=option.notes,
            )
        )
    return observations


def _accommodation_observations(trip: CandidateTrip, observed_at: datetime) -> list[PriceObservation]:
    observations = []
    for option in trip.accommodation_options:
        amount = option.total_price_amount
        if amount is None:
            continue
        observations.append(
            PriceObservation(
                watched_trip=trip.name,
                category=CostCategory.ACCOMMODATION,
                label=option.name,
                source=option.source,
                amount=amount,
                currency=option.price_currency,
                observed_at=observed_at,
                url=option.booking_url,
                notes=option.notes,
            )
        )
    return observations


def _event_observations(trip: CandidateTrip, observed_at: datetime) -> list[PriceObservation]:
    observations = []
    for event in trip.event_options:
        if event.estimated_price_amount is None:
            continue
        observations.append(
            PriceObservation(
                watched_trip=trip.name,
                category=CostCategory.EVENT,
                label=event.artist,
                source=event.source,
                amount=event.estimated_price_amount,
                currency=event.estimated_price_currency,
                observed_at=observed_at,
                url=event.ticket_url,
                notes=event.relevance_reason,
            )
        )
    return observations


def _observation_key(observation: PriceObservation) -> tuple[str, str, str, str, float, str]:
    return (
        observation.watched_trip.casefold(),
        observation.category.value,
        observation.label.casefold(),
        observation.observed_at.isoformat(),
        observation.amount,
        observation.currency,
    )
