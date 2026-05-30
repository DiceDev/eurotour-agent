from __future__ import annotations

from datetime import timedelta

from .models import WatchedTrip, Watchlist


def render_research_brief(watchlist: Watchlist, trip: WatchedTrip) -> str:
    return "\n".join(
        [
            f"# Research Brief: {trip.name}",
            "",
            f"- Home base: {watchlist.profile.home_city}",
            f"- Destination: {trip.destination}",
            f"- Date window: {trip.earliest_start} to {trip.latest_end}",
            f"- Trip length: {trip.nights_min}-{trip.nights_max} nights",
            f"- Budget limit: {_format_budget(trip, watchlist)}",
            f"- Preferred airports: {', '.join(watchlist.profile.preferred_airports) or 'none'}",
            f"- Preferred stations: {', '.join(watchlist.profile.preferred_stations) or 'none'}",
            f"- Music genres: {', '.join(watchlist.music.genres) or 'none'}",
            f"- Priority artists: {', '.join(watchlist.music.priority_artists) or 'none'}",
            "",
            "## Search Tasks",
            "",
            "### Calendar",
            "- Confirm free windows that fit the trip length.",
            "- Check whether travel time eats into important work or recovery time.",
            "",
            "### Transport",
            *_transport_tasks(watchlist, trip),
            "",
            "### Concerts",
            *_concert_tasks(trip),
            "",
            "### Accommodation",
            *_accommodation_tasks(trip),
            "",
            "### Local Costs",
            "- Estimate airport/station transfers and local transit passes.",
            "- Estimate food/drink by day count.",
            "- Add a buffer for luggage storage, taxis, fees, and small schedule failures.",
            "",
            "## Output Files",
            "",
            f"- Transport options: `local/{_slug(trip.name)}.transport.yaml`",
            f"- Accommodation options: `local/{_slug(trip.name)}.accommodation.yaml`",
            f"- Event options: `local/{_slug(trip.name)}.events.yaml`",
            f"- Merged findings: `local/{_slug(trip.name)}.findings.yaml`",
            "",
        ]
    )


def transport_template(watchlist: Watchlist, trip: WatchedTrip) -> dict:
    origin_airport = watchlist.profile.preferred_airports[0] if watchlist.profile.preferred_airports else watchlist.profile.home_city
    origin_station = watchlist.profile.preferred_stations[0] if watchlist.profile.preferred_stations else watchlist.profile.home_city
    return {
        "transport_options": [
            {
                "mode": "flight",
                "origin": origin_airport,
                "destination": trip.destination,
                "source": "manual",
                "provider": None,
                "departs_at": None,
                "arrives_at": None,
                "price_amount": None,
                "price_currency": watchlist.profile.default_currency,
                "total_travel_time_hours": None,
                "baggage_included": None,
                "booking_confidence": 0.5,
                "booking_url": None,
                "notes": "Verify fare, baggage, and airport transfer time on primary source.",
            },
            {
                "mode": "train",
                "origin": origin_station,
                "destination": trip.destination,
                "source": "manual",
                "provider": None,
                "departs_at": None,
                "arrives_at": None,
                "price_amount": None,
                "price_currency": watchlist.profile.default_currency,
                "total_travel_time_hours": None,
                "baggage_included": True,
                "booking_confidence": 0.5,
                "booking_url": None,
                "notes": "Verify rail fare, changes, and city-centre arrival time.",
            },
            {
                "mode": "coach",
                "origin": watchlist.profile.home_city,
                "destination": trip.destination,
                "source": "manual",
                "provider": None,
                "departs_at": None,
                "arrives_at": None,
                "price_amount": None,
                "price_currency": watchlist.profile.default_currency,
                "total_travel_time_hours": None,
                "baggage_included": True,
                "booking_confidence": 0.25,
                "booking_url": None,
                "notes": "Use as fallback or price floor; penalize brutal travel times.",
            },
        ]
    }


def accommodation_template(watchlist: Watchlist, trip: WatchedTrip) -> dict:
    check_in = trip.earliest_start
    check_out = check_in + timedelta(days=trip.nights_min)
    return {
        "accommodation_options": [
            {
                "name": f"{trip.destination} accommodation option",
                "city": trip.destination,
                "source": "manual",
                "area": None,
                "check_in": check_in.isoformat(),
                "check_out": check_out.isoformat(),
                "nightly_price_amount": None,
                "total_price_amount": None,
                "price_currency": watchlist.profile.default_currency,
                "refundable": None,
                "booking_confidence": 0.5,
                "booking_url": None,
                "notes": "Prefer refundable until transport and event tickets are verified.",
            }
        ]
    }


def events_template(watchlist: Watchlist, trip: WatchedTrip) -> dict:
    return {
        "event_options": [
            {
                "artist": "Artist or event name",
                "city": trip.destination,
                "source": "manual",
                "venue": None,
                "event_date": trip.earliest_start.isoformat(),
                "ticket_url": None,
                "ticket_status": None,
                "estimated_price_amount": None,
                "estimated_price_currency": watchlist.profile.default_currency,
                "relevance_score": 0.5,
                "relevance_reason": "Explain why this event fits the music profile.",
            }
        ]
    }


def _transport_tasks(watchlist: Watchlist, trip: WatchedTrip) -> list[str]:
    tasks: list[str] = []
    if trip.watch.flights:
        for airport in watchlist.profile.preferred_airports[:3]:
            tasks.append(f"- Search flights from {airport} to {trip.destination} across the date window.")
    if trip.watch.trains:
        for station in watchlist.profile.preferred_stations[:2]:
            tasks.append(f"- Search rail from {station} to {trip.destination}, including Eurostar where relevant.")
    tasks.append(f"- Search coaches from {watchlist.profile.home_city} to {trip.destination} as a fallback benchmark.")
    return tasks


def _concert_tasks(trip: WatchedTrip) -> list[str]:
    if not trip.watch.concerts:
        return ["- Concert tracking disabled for this trip."]
    return [
        "- Search Spotify Live Events for followed/top artists.",
        "- Search Ticketmaster, Songkick, Bandsintown, DICE, Resident Advisor, Eventbrite, and venue calendars.",
        "- Record primary ticket links and price/fee confidence.",
    ]


def _accommodation_tasks(trip: WatchedTrip) -> list[str]:
    return [
        f"- Search {trip.destination} lodging for each plausible trip length.",
        "- Prefer refundable private room/hotel options until anchors are verified.",
        "- Record total stay cost, taxes/fees, area, cancellation terms, and venue/transit convenience.",
    ]


def _format_budget(trip: WatchedTrip, watchlist: Watchlist) -> str:
    if trip.budget_limit is None:
        return "not set"
    return f"{trip.budget_limit:.2f} {watchlist.profile.default_currency}"


def _slug(value: str) -> str:
    return "".join(character.lower() if character.isalnum() else "-" for character in value).strip("-")
