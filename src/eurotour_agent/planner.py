from __future__ import annotations

from .history import history_reasons, history_risks, history_score_adjustment
from .models import (
    CalendarWindow,
    CandidateTrip,
    CostCategory,
    CostComponent,
    CurrencyRateSnapshot,
    Recommendation,
    RecommendationDecision,
    TripHistory,
)


def rank_candidate_trips(
    calendar_windows: list[CalendarWindow],
    candidate_trips: list[CandidateTrip],
    currency_rates: CurrencyRateSnapshot | None = None,
    trip_history: TripHistory | None = None,
) -> list[Recommendation]:
    recommendations: list[Recommendation] = []

    for trip in candidate_trips:
        best_event = max((event.relevance_score for event in trip.event_options), default=0.0)
        best_transport = _best_transport_score(trip)
        calendar_score = _calendar_score(trip, calendar_windows)
        budget_score = _budget_score(trip, currency_rates)
        base_score = best_event * 0.35 + best_transport * 0.25 + calendar_score * 0.2 + budget_score * 0.2
        score = round(max(0.0, min(base_score + history_score_adjustment(trip_history, trip.destination), 1.0)), 3)
        estimated_total, estimated_currency = _estimated_total(trip, currency_rates)
        cost_breakdown = _cost_breakdown(trip)
        missing_cost_categories = _missing_cost_categories(trip)
        decision = _decision_for_score(
            score=score,
            trip=trip,
            calendar_windows=calendar_windows,
            missing_cost_categories=missing_cost_categories,
            estimated_currency=estimated_currency,
        )
        reasons = _reasons(trip=trip, score=score, estimated_total=estimated_total, estimated_currency=estimated_currency)
        reasons.extend(history_reasons(trip_history, trip.destination))
        risks = _risks(trip=trip, calendar_windows=calendar_windows, currency_rates=currency_rates)
        risks.extend(history_risks(trip_history, trip.destination))

        recommendations.append(
            Recommendation(
                trip_name=trip.name,
                destination=trip.destination,
                decision=decision,
                title=f"{_decision_label(decision)} {trip.destination}",
                summary=(
                    f"{trip.destination} from {trip.start_date} to {trip.end_date}: "
                    f"{len(trip.transport_options)} transport option(s), "
                    f"{len(trip.event_options)} event option(s), score {score:.3f}."
                ),
                score=score,
                estimated_total_amount=estimated_total,
                estimated_total_currency=estimated_currency or trip.budget_currency,
                estimate_complete=not missing_cost_categories,
                missing_cost_categories=missing_cost_categories,
                cost_breakdown=cost_breakdown,
                reasons=reasons,
                risks=risks,
                next_actions=_next_actions(decision),
            )
        )

    return sorted(recommendations, key=lambda item: item.score, reverse=True)


def _best_transport_score(trip: CandidateTrip) -> float:
    if not trip.transport_options:
        return 0.0

    scores: list[float] = []
    for option in trip.transport_options:
        score = option.booking_confidence * 0.4 + 0.25
        if option.total_travel_time_hours is not None:
            score += max(0, 0.25 - option.total_travel_time_hours / 40)
        if option.baggage_included is True:
            score += 0.1
        elif option.baggage_included is None:
            score -= 0.05
        scores.append(max(0.0, min(score, 1.0)))
    return max(scores)


def _calendar_score(trip: CandidateTrip, calendar_windows: list[CalendarWindow]) -> float:
    if trip.calendar_fit is True:
        return 1.0
    if trip.calendar_fit is False:
        return 0.0
    if _trip_fits_any_calendar_window(trip, calendar_windows):
        return 0.85
    return 0.2


def _budget_score(trip: CandidateTrip, currency_rates: CurrencyRateSnapshot | None) -> float:
    estimated_total, estimated_currency = _estimated_total(trip, currency_rates)
    if estimated_total is None or trip.budget_limit_amount is None:
        return 0.45
    if estimated_currency != trip.budget_currency:
        return 0.45
    if estimated_total <= trip.budget_limit_amount:
        return 1.0
    overage = estimated_total - trip.budget_limit_amount
    return max(0.0, 1.0 - overage / trip.budget_limit_amount)


def _estimated_total(
    trip: CandidateTrip,
    currency_rates: CurrencyRateSnapshot | None = None,
) -> tuple[float | None, str | None]:
    components = _cost_breakdown(trip)
    converted_amounts: list[float] = []
    source_currencies = {component.currency for component in components if component.amount is not None}
    if not source_currencies:
        return None, trip.budget_currency

    for component in components:
        if component.amount is None:
            continue
        if component.currency == trip.budget_currency:
            converted_amounts.append(component.amount)
            continue
        converted = currency_rates.convert(component.amount, component.currency, trip.budget_currency) if currency_rates else None
        if converted is None:
            return None, "MIXED"
        converted_amounts.append(converted)

    return round(sum(converted_amounts), 2), trip.budget_currency


def _cost_breakdown(trip: CandidateTrip) -> list[CostComponent]:
    components: list[CostComponent] = []
    selected_transport = _selected_transport(trip)
    selected_event = _selected_event(trip)
    selected_accommodation = _selected_accommodation(trip)

    if selected_transport and selected_transport.price_amount is not None:
        components.append(
            CostComponent(
                category=CostCategory.TRANSPORT,
                label=f"{selected_transport.mode}: {selected_transport.origin} to {selected_transport.destination}",
                source=selected_transport.source,
                amount=selected_transport.price_amount,
                currency=selected_transport.price_currency,
                confidence=selected_transport.booking_confidence,
                notes=selected_transport.notes,
            )
        )
    if selected_accommodation and selected_accommodation.total_price_amount is not None:
        components.append(
            CostComponent(
                category=CostCategory.ACCOMMODATION,
                label=selected_accommodation.name,
                source=selected_accommodation.source,
                amount=selected_accommodation.total_price_amount,
                currency=selected_accommodation.price_currency,
                confidence=selected_accommodation.booking_confidence,
                notes=selected_accommodation.notes,
            )
        )
    if selected_event and selected_event.estimated_price_amount is not None:
        components.append(
            CostComponent(
                category=CostCategory.EVENT,
                label=selected_event.artist,
                source=selected_event.source,
                amount=selected_event.estimated_price_amount,
                currency=selected_event.estimated_price_currency,
                confidence=selected_event.relevance_score,
                notes=selected_event.relevance_reason,
            )
        )
    components.extend(trip.cost_components)
    return components


def _decision_for_score(
    score: float,
    trip: CandidateTrip,
    calendar_windows: list[CalendarWindow],
    missing_cost_categories: list[CostCategory],
    estimated_currency: str | None,
) -> RecommendationDecision:
    if trip.calendar_fit is False:
        return RecommendationDecision.IGNORE
    if _is_over_budget(trip):
        return RecommendationDecision.WATCH if score >= 0.35 else RecommendationDecision.IGNORE
    if missing_cost_categories or estimated_currency == "MIXED":
        return RecommendationDecision.RESEARCH_NEEDED if score >= 0.55 else RecommendationDecision.WATCH
    if score >= 0.76 and (trip.calendar_fit is True or _trip_fits_any_calendar_window(trip, calendar_windows)):
        return RecommendationDecision.READY_TO_VERIFY
    if score >= 0.35:
        return RecommendationDecision.WATCH
    return RecommendationDecision.IGNORE


def _reasons(
    trip: CandidateTrip,
    score: float,
    estimated_total: float | None,
    estimated_currency: str | None,
) -> list[str]:
    reasons = [f"Composite score is {score:.3f}."]
    if trip.event_options:
        event = _selected_event(trip)
        reasons.append(f"Best event signal is {event.artist} in {event.city} with relevance {event.relevance_score:.2f}.")
    if trip.transport_options:
        best_transport = min(
            trip.transport_options,
            key=lambda item: item.price_amount if item.price_amount is not None else float("inf"),
        )
        if best_transport.price_amount is not None:
            reasons.append(
                f"Lowest tracked {best_transport.mode} option is {best_transport.price_amount:.2f} {best_transport.price_currency}."
            )
    if estimated_total is not None and trip.budget_limit_amount is not None:
        if estimated_currency == trip.budget_currency:
            reasons.append(
                f"Estimated tracked cost is {estimated_total:.2f} {estimated_currency} against budget {trip.budget_limit_amount:.2f}."
            )
        else:
            reasons.append(
                f"Estimated tracked cost is {estimated_total:.2f} {estimated_currency}; budget is in {trip.budget_currency}, so conversion is needed."
            )
    return reasons


def _risks(
    trip: CandidateTrip,
    calendar_windows: list[CalendarWindow],
    currency_rates: CurrencyRateSnapshot | None,
) -> list[str]:
    risks: list[str] = []
    if trip.calendar_fit is None and not _trip_fits_any_calendar_window(trip, calendar_windows):
        risks.append("Calendar fit has not been verified.")
    if any(option.source == "fixture" for option in trip.transport_options):
        risks.append("Transport prices are fixture estimates, not live fares.")
    if any(event.source == "fixture" for event in trip.event_options):
        risks.append("Concert data is fixture output, not live inventory.")
    if any(option.source == "fixture" for option in trip.accommodation_options):
        risks.append("Accommodation prices are fixture estimates, not live room rates.")
    if any(option.source == "manual" for option in trip.transport_options) or any(
        event.source == "manual" for event in trip.event_options
    ) or any(
        option.source == "manual" for option in trip.accommodation_options
    ):
        risks.append("Manual findings need primary-source re-check before money changes hands.")
    _, estimated_currency = _estimated_total(trip, currency_rates)
    if estimated_currency not in {None, trip.budget_currency}:
        risks.append("Tracked costs are not in the budget currency; convert before treating the budget score as reliable.")
    missing_cost_categories = _missing_cost_categories(trip)
    if missing_cost_categories:
        missing = ", ".join(category.value for category in missing_cost_categories)
        risks.append(f"Total trip estimate is incomplete; missing priced categories: {missing}.")
    if _is_over_budget(trip, currency_rates):
        risks.append("Estimated tracked cost is above the trip budget.")
    if any(option.baggage_included is None for option in trip.transport_options):
        risks.append("Baggage and fare restrictions need primary-source verification.")
    if not trip.transport_options:
        risks.append("No transport option is attached.")
    if not trip.event_options:
        risks.append("No concert or music event option is attached.")
    if not trip.accommodation_options:
        risks.append("No accommodation option is attached.")
    return risks


def _trip_fits_any_calendar_window(trip: CandidateTrip, calendar_windows: list[CalendarWindow]) -> bool:
    for window in calendar_windows:
        if window.starts_at.date() <= trip.start_date and window.ends_at.date() >= trip.end_date:
            return True
    return False


def _selected_event(trip: CandidateTrip):
    if not trip.event_options:
        return None
    return max(trip.event_options, key=lambda item: item.relevance_score)


def _selected_transport(trip: CandidateTrip):
    priced = [option for option in trip.transport_options if option.price_amount is not None]
    if priced:
        return min(priced, key=lambda item: item.price_amount)
    if trip.transport_options:
        return max(trip.transport_options, key=lambda item: item.booking_confidence)
    return None


def _selected_accommodation(trip: CandidateTrip):
    priced = [option for option in trip.accommodation_options if option.total_price_amount is not None]
    if priced:
        return min(priced, key=lambda item: item.total_price_amount)
    if trip.accommodation_options:
        return max(trip.accommodation_options, key=lambda item: item.booking_confidence)
    return None


def _missing_cost_categories(trip: CandidateTrip) -> list[CostCategory]:
    components = _cost_breakdown(trip)
    priced_categories = {component.category for component in components if component.amount is not None}
    required = [
        CostCategory.TRANSPORT,
        CostCategory.ACCOMMODATION,
        CostCategory.EVENT,
        CostCategory.LOCAL_TRANSIT,
        CostCategory.FOOD_DRINK,
        CostCategory.BUFFER,
    ]
    return [category for category in required if category not in priced_categories]


def _next_actions(decision: RecommendationDecision) -> list[str]:
    if decision == RecommendationDecision.READY_TO_VERIFY:
        return [
            "Verify calendar availability.",
            "Confirm fare and ticket availability on primary sources.",
            "Prepare booking checklist; do not purchase automatically.",
        ]
    if decision == RecommendationDecision.RESEARCH_NEEDED:
        return [
            "Fill missing cost categories and currency rates.",
            "Refresh primary-source fares, rooms, and ticket prices.",
            "Re-rank after the estimate is complete.",
        ]
    if decision == RecommendationDecision.WATCH:
        return [
            "Refresh transport prices from primary or aggregator sources.",
            "Refresh concert discovery from Spotify, Bandsintown, Songkick, DICE, RA, and venue calendars.",
            "Re-rank after calendar fit is confirmed.",
        ]
    return [
        "Archive or lower priority unless new dates, prices, or events appear.",
    ]


def _decision_label(decision: RecommendationDecision) -> str:
    labels = {
        RecommendationDecision.READY_TO_VERIFY: "Ready to verify",
        RecommendationDecision.RESEARCH_NEEDED: "Research needed",
        RecommendationDecision.WATCH: "Watch",
        RecommendationDecision.IGNORE: "Ignore",
    }
    return labels[decision]


def _is_over_budget(trip: CandidateTrip, currency_rates: CurrencyRateSnapshot | None = None) -> bool:
    estimated_total, estimated_currency = _estimated_total(trip, currency_rates)
    return (
        estimated_total is not None
        and trip.budget_limit_amount is not None
        and estimated_currency == trip.budget_currency
        and estimated_total > trip.budget_limit_amount
    )
