from __future__ import annotations

from datetime import date

import requests

from eurotour_agent.models import EventOption

DISCOVERY_URL = "https://app.ticketmaster.com/discovery/v2/events.json"


def search_music_events(
    api_key: str,
    city: str,
    starts_on: date,
    ends_on: date,
    size: int = 20,
) -> list[EventOption]:
    response = requests.get(
        DISCOVERY_URL,
        params={
            "apikey": api_key,
            "city": city,
            "startDateTime": f"{starts_on.isoformat()}T00:00:00Z",
            "endDateTime": f"{ends_on.isoformat()}T23:59:59Z",
            "classificationName": "music",
            "size": size,
            "sort": "date,asc",
        },
        timeout=30,
    )
    response.raise_for_status()
    events = response.json().get("_embedded", {}).get("events", [])
    return [_event_from_ticketmaster(item, city) for item in events]


def _event_from_ticketmaster(item: dict, fallback_city: str) -> EventOption:
    dates = item.get("dates", {}).get("start", {})
    local_date = dates.get("localDate")
    embedded = item.get("_embedded", {})
    venues = embedded.get("venues", [])
    attractions = embedded.get("attractions", [])
    venue = venues[0].get("name") if venues else None
    city = venues[0].get("city", {}).get("name") if venues else fallback_city
    artist = attractions[0].get("name") if attractions else item.get("name", "Unknown event")
    price_ranges = item.get("priceRanges") or []
    min_price = price_ranges[0].get("min") if price_ranges else None
    currency = price_ranges[0].get("currency", "USD") if price_ranges else "USD"

    return EventOption(
        artist=artist,
        city=city,
        source="ticketmaster",
        venue=venue,
        event_date=date.fromisoformat(local_date),
        ticket_url=item.get("url"),
        ticket_status=item.get("dates", {}).get("status", {}).get("code"),
        estimated_price_amount=min_price,
        estimated_price_currency=currency,
        relevance_score=0.45,
        relevance_reason="Ticketmaster music event; boost with Spotify taste or manual review.",
    )
