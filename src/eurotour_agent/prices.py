from __future__ import annotations

from collections import defaultdict

from .models import PriceAlert, PriceHistory, PriceObservation


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
