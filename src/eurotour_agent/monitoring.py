from __future__ import annotations

from .destinations import suggest_destinations
from .models import PriceHistory, RecommendationDecision, ResearchRun, TripHistory
from .planner import rank_candidate_trips
from .prices import price_alerts
from .providers.registry import source_reliability


def render_monitoring_brief(
    research_run: ResearchRun,
    trip_history: TripHistory | None = None,
    price_history: PriceHistory | None = None,
    destination_limit: int = 5,
    drop_threshold_percent: float = 10.0,
) -> str:
    effective_history = trip_history or research_run.trip_history
    recommendations = rank_candidate_trips(
        calendar_windows=research_run.calendar_windows,
        candidate_trips=research_run.candidate_trips,
        currency_rates=research_run.currency_rates,
        trip_history=effective_history,
    )
    alerts = price_alerts(price_history, drop_threshold_percent=drop_threshold_percent) if price_history else []
    destinations = suggest_destinations(effective_history, limit=destination_limit) if effective_history else []

    lines = [
        "# EuroTour Monitoring Brief",
        "",
        f"- Generated: {research_run.generated_at.isoformat()}",
        f"- Candidate trips: {len(recommendations)}",
        f"- Price alerts: {len(alerts)}",
        f"- Destination ideas: {len(destinations)}",
        "",
    ]

    lines.extend(["## Top Recommendations", ""])
    if recommendations:
        for recommendation in recommendations[:5]:
            lines.append(
                f"- {recommendation.destination}: {recommendation.decision.value}, "
                f"score {recommendation.score:.3f}, {recommendation.estimated_total_amount or 'unknown'} "
                f"{recommendation.estimated_total_currency}"
            )
    else:
        lines.append("- No candidate trips found.")
    lines.append("")

    lines.extend(["## Source Quality", ""])
    quality = _source_quality(research_run)
    if quality:
        for source, score in quality:
            lines.append(f"- {source}: reliability {score:.2f}")
    else:
        lines.append("- No priced or event sources found.")
    lines.append("")

    lines.extend(["## Price Alerts", ""])
    if alerts:
        for alert in alerts:
            drop = "new low" if alert.is_new_low else f"{alert.drop_percent:.1f}% drop"
            lines.append(
                f"- {alert.watched_trip}: {alert.label} is {alert.current_amount:.2f} {alert.currency} ({drop}). "
                f"{alert.reason}"
            )
    else:
        lines.append("- No latest price drops or new lows found.")
    lines.append("")

    lines.extend(["## Destination Ideas", ""])
    if destinations:
        for destination in destinations:
            tags = ", ".join(destination.matched_tags) if destination.matched_tags else "variety"
            lines.append(f"- {destination.city}, {destination.country}: score {destination.score:.3f}; {tags}.")
    else:
        lines.append("- No trip history available for destination ideas.")
    lines.append("")

    lines.extend(["## Next Actions", ""])
    if alerts:
        lines.append("- Verify alerting fares or room rates on primary sources before booking.")
    if any(recommendation.decision == RecommendationDecision.RESEARCH_NEEDED for recommendation in recommendations):
        lines.append("- Fill missing cost categories for top `research_needed` trips.")
    elif recommendations:
        lines.append("- Refresh watched trips after primary-source price and event checks.")
    if destinations:
        lines.append("- Draft one or two destination ideas into the watchlist if they fit the calendar.")
    if not alerts and not recommendations and not destinations:
        lines.append("- Add watchlist, history, or price data; the agent has nothing useful to chew on.")
    lines.append("")
    return "\n".join(lines)


def _source_quality(research_run: ResearchRun) -> list[tuple[str, float]]:
    sources: set[str] = set()
    for trip in research_run.candidate_trips:
        sources.update(option.source for option in trip.transport_options)
        sources.update(option.source for option in trip.accommodation_options)
        sources.update(event.source for event in trip.event_options)
        sources.update(component.source for component in trip.cost_components)
    return sorted(((source, source_reliability(source)) for source in sources), key=lambda item: item[1], reverse=True)
