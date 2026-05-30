from __future__ import annotations

from datetime import UTC, datetime, timedelta

from .models import ResearchRun
from .planner import rank_candidate_trips


def audit_research_run(research_run: ResearchRun, stale_after_days: int = 7) -> list[str]:
    issues: list[str] = []
    now = datetime.now(UTC)
    stale_before = now - timedelta(days=stale_after_days)
    recommendations = rank_candidate_trips(
        calendar_windows=research_run.calendar_windows,
        candidate_trips=research_run.candidate_trips,
        currency_rates=research_run.currency_rates,
    )

    for recommendation in recommendations:
        if not recommendation.estimate_complete:
            missing = ", ".join(category.value for category in recommendation.missing_cost_categories)
            issues.append(f"{recommendation.trip_name}: estimate incomplete ({missing}).")

    for trip in research_run.candidate_trips:
        if trip.calendar_fit is None and not research_run.calendar_windows:
            issues.append(f"{trip.name}: calendar fit is not verified.")
        for option in trip.transport_options:
            if option.source == "fixture":
                issues.append(f"{trip.name}: transport option {option.mode} is fixture data.")
            if option.price_amount is None:
                issues.append(f"{trip.name}: transport option {option.mode} is missing price.")
            if option.booking_url is None:
                issues.append(f"{trip.name}: transport option {option.mode} is missing booking URL.")
            observed_at = option.observed_at
            if observed_at.tzinfo is None:
                observed_at = observed_at.replace(tzinfo=UTC)
            if observed_at < stale_before:
                issues.append(f"{trip.name}: transport option {option.mode} is stale.")
        for option in trip.accommodation_options:
            if option.source == "fixture":
                issues.append(f"{trip.name}: accommodation option is fixture data.")
            if option.total_price_amount is None:
                issues.append(f"{trip.name}: accommodation option {option.name} is missing total price.")
            if option.booking_url is None:
                issues.append(f"{trip.name}: accommodation option {option.name} is missing booking URL.")
        for event in trip.event_options:
            if event.source == "fixture":
                issues.append(f"{trip.name}: event option {event.artist} is fixture data.")
            if event.estimated_price_amount is None:
                issues.append(f"{trip.name}: event option {event.artist} is missing ticket price.")
            if event.ticket_url is None:
                issues.append(f"{trip.name}: event option {event.artist} is missing ticket URL.")

    return issues
