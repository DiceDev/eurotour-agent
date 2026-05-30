from __future__ import annotations

from datetime import datetime

import requests

from eurotour_agent.models import TransportOption

TOKEN_URL = "https://test.api.amadeus.com/v1/security/oauth2/token"
FLIGHT_OFFERS_URL = "https://test.api.amadeus.com/v2/shopping/flight-offers"


def request_access_token(client_id: str, client_secret: str) -> dict:
    response = requests.post(
        TOKEN_URL,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        },
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def search_flight_offers(
    access_token: str,
    origin: str,
    destination: str,
    departure_date: str,
    return_date: str | None = None,
    adults: int = 1,
    currency: str | None = None,
    max_results: int = 10,
    non_stop: bool | None = None,
) -> list[TransportOption]:
    params: dict[str, str | int | bool] = {
        "originLocationCode": origin,
        "destinationLocationCode": destination,
        "departureDate": departure_date,
        "adults": adults,
        "max": max_results,
    }
    if return_date:
        params["returnDate"] = return_date
    if currency:
        params["currencyCode"] = currency
    if non_stop is not None:
        params["nonStop"] = "true" if non_stop else "false"
    response = requests.get(
        FLIGHT_OFFERS_URL,
        params=params,
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=30,
    )
    response.raise_for_status()
    return [_transport_from_offer(offer) for offer in response.json().get("data", [])]


def _transport_from_offer(offer: dict) -> TransportOption:
    itineraries = offer.get("itineraries") or []
    first_itinerary = itineraries[0] if itineraries else {}
    segments = first_itinerary.get("segments") or []
    first_segment = segments[0] if segments else {}
    last_segment = segments[-1] if segments else {}
    price = offer.get("price") or {}
    validating_carriers = offer.get("validatingAirlineCodes") or []
    price_amount = _float_or_none(price.get("grandTotal") or price.get("total"))
    duration_hours = _duration_to_hours(first_itinerary.get("duration"))
    baggage_included = _baggage_included(offer)

    return TransportOption(
        mode="flight",
        origin=first_segment.get("departure", {}).get("iataCode", "unknown"),
        destination=last_segment.get("arrival", {}).get("iataCode", "unknown"),
        source="amadeus",
        provider=", ".join(validating_carriers) if validating_carriers else "amadeus",
        departs_at=_parse_amadeus_datetime(first_segment.get("departure", {}).get("at")),
        arrives_at=_parse_amadeus_datetime(last_segment.get("arrival", {}).get("at")),
        price_amount=price_amount,
        price_currency=price.get("currency", "USD"),
        total_travel_time_hours=duration_hours,
        baggage_included=baggage_included,
        booking_confidence=0.68,
        booking_url=None,
        notes="Amadeus Flight Offers Search result; confirm current fare with Flight Offers Price before booking.",
    )


def _float_or_none(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _parse_amadeus_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _duration_to_hours(duration: str | None) -> float | None:
    if not duration or not duration.startswith("PT"):
        return None
    remaining = duration[2:]
    hours = 0
    minutes = 0
    if "H" in remaining:
        raw_hours, remaining = remaining.split("H", 1)
        hours = int(raw_hours or 0)
    if "M" in remaining:
        raw_minutes = remaining.split("M", 1)[0]
        minutes = int(raw_minutes or 0)
    return round(hours + minutes / 60, 2)


def _baggage_included(offer: dict) -> bool | None:
    pricings = offer.get("travelerPricings") or []
    for pricing in pricings:
        for fare_detail in pricing.get("fareDetailsBySegment") or []:
            checked_bags = fare_detail.get("includedCheckedBags") or {}
            quantity = checked_bags.get("quantity")
            weight = checked_bags.get("weight")
            if quantity is not None:
                return int(quantity) > 0
            if weight is not None:
                return float(weight) > 0
    return None
