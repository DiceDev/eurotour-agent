from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta

from .models import (
    AccommodationOption,
    CandidateTrip,
    CostCategory,
    CostComponent,
    CurrencyRateSnapshot,
    EventOption,
    ManualFindings,
    MusicTasteProfile,
    ResearchRun,
    TransportOption,
    TripHistory,
    WatchedTrip,
    Watchlist,
)


def build_research_run(
    watchlist: Watchlist,
    watchlist_path: str,
    trip_name: str | None = None,
    dry_run: bool = True,
    manual_findings: ManualFindings | None = None,
    music_taste: MusicTasteProfile | None = None,
    currency_rates: CurrencyRateSnapshot | None = None,
    trip_history: TripHistory | None = None,
) -> ResearchRun:
    selected_trips = [
        trip for trip in watchlist.watched_trips if trip_name is None or trip.name.lower() == trip_name.lower()
    ]

    candidate_trips = []
    for trip in selected_trips:
        findings = _findings_for_trip(manual_findings, trip)
        candidate_trips.append(
            _candidate_from_watched_trip(
                watchlist=watchlist,
                trip=trip,
                dry_run=dry_run,
                findings=findings,
                music_taste=music_taste,
            )
        )

    return ResearchRun(
        generated_at=datetime.now(UTC),
        mode=_run_mode(dry_run=dry_run, manual_findings=manual_findings),
        watchlist_path=watchlist_path,
        calendar_windows=manual_findings.calendar_windows if manual_findings else [],
        currency_rates=currency_rates,
        trip_history=trip_history,
        candidate_trips=candidate_trips,
        source_notes=[
            "Dry-run data is deterministic fixture output for workflow validation.",
            "Manual findings are treated as user/chat-researched provisional data.",
            "Verify fares and tickets against primary airline, operator, venue, or ticketing pages before acting.",
        ],
    )


def _candidate_from_watched_trip(
    watchlist: Watchlist,
    trip: WatchedTrip,
    dry_run: bool,
    findings: object | None,
    music_taste: MusicTasteProfile | None,
) -> CandidateTrip:
    start_date = findings.start_date if findings is not None and findings.start_date else trip.earliest_start
    end_date = (
        findings.end_date
        if findings is not None and findings.end_date
        else min(trip.latest_end, start_date + timedelta(days=trip.nights_min))
    )
    observed_at = datetime.now(UTC)

    transport_options: list[TransportOption] = []
    if trip.watch.flights:
        transport_options.append(_fixture_flight(watchlist, trip, start_date, observed_at))
    if trip.watch.trains:
        transport_options.append(_fixture_train(watchlist, trip, start_date, observed_at))

    event_options = [_fixture_event(watchlist, trip, start_date)] if trip.watch.concerts else []
    accommodation_options = [_fixture_accommodation(watchlist, trip, start_date, end_date)]
    cost_components = _fixture_cost_components(watchlist, trip, start_date, end_date)
    if findings is not None:
        if findings.transport_options:
            transport_options = findings.transport_options
        if findings.event_options:
            event_options = findings.event_options
        if findings.accommodation_options:
            accommodation_options = findings.accommodation_options
        if findings.cost_components:
            cost_components = findings.cost_components
        event_options = _dedupe_events(event_options)
    if music_taste is not None:
        event_options = _apply_music_taste(event_options, music_taste)

    return CandidateTrip(
        name=trip.name,
        destination=trip.destination,
        start_date=start_date,
        end_date=end_date,
        reason=trip.notes or "Tracked from watchlist.",
        budget_limit_amount=trip.budget_limit,
        budget_currency=watchlist.profile.default_currency,
        transport_options=transport_options,
        event_options=event_options,
        accommodation_options=accommodation_options,
        cost_components=cost_components,
        calendar_fit=findings.calendar_fit if findings is not None else None,
        source_notes=[
            "No calendar connector was queried in this dry run.",
            "No purchase or booking action was attempted.",
            *(findings.notes if findings is not None else []),
        ],
    )


def _run_mode(dry_run: bool, manual_findings: ManualFindings | None) -> str:
    if dry_run and manual_findings:
        return "dry-run-fixture-plus-manual"
    if dry_run:
        return "dry-run-fixture"
    if manual_findings:
        return "live-provider-placeholder-plus-manual"
    return "live-provider-placeholder"


def _findings_for_trip(manual_findings: ManualFindings | None, trip: WatchedTrip):
    if manual_findings is None:
        return None
    return manual_findings.trips.get(trip.name) or manual_findings.trips.get(trip.destination)


def _dedupe_events(events: list[EventOption]) -> list[EventOption]:
    seen: set[tuple[str, str, date, str | None]] = set()
    deduped: list[EventOption] = []
    for event in events:
        key = (
            event.artist.casefold(),
            event.city.casefold(),
            event.event_date,
            event.venue.casefold() if event.venue else None,
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(event)
    return deduped


def _apply_music_taste(events: list[EventOption], music_taste: MusicTasteProfile) -> list[EventOption]:
    artist_weights = {artist.name.casefold(): artist.weight for artist in music_taste.artists}
    updated: list[EventOption] = []
    for event in events:
        matched_artist, weight = _taste_match(event.artist, artist_weights)
        if matched_artist is None or weight is None:
            updated.append(event)
            continue
        boosted = event.model_copy(
            update={
                "relevance_score": min(1.0, max(event.relevance_score, 0.65 + weight * 0.3)),
                "relevance_reason": f"{event.relevance_reason or 'Event matched music taste.'} Spotify taste match: {matched_artist}.",
            }
        )
        updated.append(boosted)
    return updated


def _taste_match(event_artist: str, artist_weights: dict[str, float]) -> tuple[str | None, float | None]:
    event_name = event_artist.casefold()
    if event_name in artist_weights:
        return event_artist, artist_weights[event_name]
    for artist_name, weight in artist_weights.items():
        if artist_name in event_name:
            return artist_name, weight
    return None, None


def _fixture_flight(
    watchlist: Watchlist,
    trip: WatchedTrip,
    start_date: date,
    observed_at: datetime,
) -> TransportOption:
    origin = watchlist.profile.preferred_airports[0] if watchlist.profile.preferred_airports else watchlist.profile.home_city
    destination_code = trip.destination[:3].upper()
    departs_at = datetime.combine(start_date, time(hour=9), tzinfo=UTC)
    return TransportOption(
        mode="flight",
        origin=origin,
        destination=destination_code,
        source="fixture",
        provider="primary-airline-check-needed",
        departs_at=departs_at,
        arrives_at=departs_at + timedelta(hours=2, minutes=15),
        price_amount=_estimate_base_price(trip, flight=True),
        price_currency=watchlist.profile.default_currency,
        total_travel_time_hours=4.5,
        baggage_included=None,
        booking_confidence=0.45,
        booking_url=None,
        notes="Placeholder fare for scoring only; verify with Google Flights and airline site.",
        observed_at=observed_at,
    )


def _fixture_train(
    watchlist: Watchlist,
    trip: WatchedTrip,
    start_date: date,
    observed_at: datetime,
) -> TransportOption:
    origin = watchlist.profile.preferred_stations[0] if watchlist.profile.preferred_stations else watchlist.profile.home_city
    departs_at = datetime.combine(start_date, time(hour=8), tzinfo=UTC)
    return TransportOption(
        mode="train",
        origin=origin,
        destination=trip.destination,
        source="fixture",
        provider="operator-check-needed",
        departs_at=departs_at,
        arrives_at=departs_at + timedelta(hours=5, minutes=45),
        price_amount=_estimate_base_price(trip, flight=False),
        price_currency=watchlist.profile.default_currency,
        total_travel_time_hours=6.25,
        baggage_included=True,
        booking_confidence=0.5,
        booking_url=None,
        notes="Placeholder rail fare for scoring only; verify with operator or trusted rail seller.",
        observed_at=observed_at,
    )


def _fixture_event(watchlist: Watchlist, trip: WatchedTrip, start_date: date) -> EventOption:
    artist = watchlist.music.priority_artists[0] if watchlist.music.priority_artists else "Priority artist TBD"
    genre = watchlist.music.genres[0] if watchlist.music.genres else "music"
    return EventOption(
        artist=artist,
        city=trip.destination,
        source="fixture",
        venue=None,
        event_date=start_date + timedelta(days=1),
        ticket_url=None,
        ticket_status="unknown",
        estimated_price_amount=65.0,
        estimated_price_currency=watchlist.profile.default_currency,
        relevance_score=0.55 if artist == "Priority artist TBD" else 0.8,
        relevance_reason=f"Fixture event standing in for {genre} discovery; verify via Spotify, Bandsintown, Songkick, DICE, RA, and venue calendars.",
    )


def _fixture_accommodation(
    watchlist: Watchlist,
    trip: WatchedTrip,
    start_date: date,
    end_date: date,
) -> AccommodationOption:
    nights = max((end_date - start_date).days, 1)
    nightly = 130.0 if trip.destination.lower() in {"berlin", "amsterdam"} else 120.0
    return AccommodationOption(
        name="Mid-range accommodation estimate",
        city=trip.destination,
        source="fixture",
        area="central-ish",
        check_in=start_date,
        check_out=end_date,
        nightly_price_amount=nightly,
        total_price_amount=round(nightly * nights, 2),
        price_currency=watchlist.profile.default_currency,
        refundable=None,
        booking_confidence=0.35,
        booking_url=None,
        notes="Fixture accommodation estimate; verify on hotel/booking sources.",
    )


def _fixture_cost_components(
    watchlist: Watchlist,
    trip: WatchedTrip,
    start_date: date,
    end_date: date,
) -> list[CostComponent]:
    nights = max((end_date - start_date).days, 1)
    days = nights + 1
    currency = watchlist.profile.default_currency
    return [
        CostComponent(
            category=CostCategory.LOCAL_TRANSIT,
            label="Airport/station transfers and city transit estimate",
            source="fixture",
            amount=round(18 * days, 2),
            currency=currency,
            confidence=0.35,
            notes="Estimate for public transport and local transfers.",
        ),
        CostComponent(
            category=CostCategory.FOOD_DRINK,
            label="Food and drink estimate",
            source="fixture",
            amount=round(65 * days, 2),
            currency=currency,
            confidence=0.3,
            notes="Mid-range daily spend estimate.",
        ),
        CostComponent(
            category=CostCategory.BUFFER,
            label="Contingency buffer",
            source="fixture",
            amount=75,
            currency=currency,
            confidence=0.25,
            notes="Small buffer for fees, taxis, and timetable nonsense.",
        ),
    ]


def _estimate_base_price(trip: WatchedTrip, flight: bool) -> float:
    budget = trip.budget_limit or 900
    divisor = 3.8 if flight else 4.5
    return round(max(60, budget / divisor), 2)
