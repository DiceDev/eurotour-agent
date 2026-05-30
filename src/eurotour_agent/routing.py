from __future__ import annotations

from dataclasses import dataclass

from .models import WatchedTrip, Watchlist


@dataclass(frozen=True)
class RouteSeed:
    trip_name: str
    destination: str
    mode: str
    origin: str
    destination_code: str
    priority: int
    notes: str


DESTINATION_AIRPORTS: dict[str, tuple[str, ...]] = {
    "amsterdam": ("AMS",),
    "barcelona": ("BCN",),
    "berlin": ("BER",),
    "bilbao": ("BIO",),
    "bologna": ("BLQ",),
    "budapest": ("BUD",),
    "copenhagen": ("CPH",),
    "ghent": ("BRU",),
    "hamburg": ("HAM",),
    "krakow": ("KRK",),
    "leipzig": ("LEJ", "BER"),
    "lisbon": ("LIS",),
    "lyon": ("LYS",),
    "porto": ("OPO",),
    "prague": ("PRG",),
    "rotterdam": ("RTM", "AMS"),
    "valencia": ("VLC",),
    "vienna": ("VIE",),
    "warsaw": ("WAW",),
}


def route_seeds_for_trip(watchlist: Watchlist, trip: WatchedTrip) -> list[RouteSeed]:
    seeds: list[RouteSeed] = []
    if trip.watch.flights:
        for origin_index, origin in enumerate(watchlist.profile.preferred_airports):
            for destination_index, destination_code in enumerate(destination_airports(trip.destination)):
                seeds.append(
                    RouteSeed(
                        trip_name=trip.name,
                        destination=trip.destination,
                        mode="flight",
                        origin=origin,
                        destination_code=destination_code,
                        priority=origin_index * 10 + destination_index + 1,
                        notes=_flight_notes(origin, destination_code),
                    )
                )
    if trip.watch.trains:
        for station_index, station in enumerate(watchlist.profile.preferred_stations):
            seeds.append(
                RouteSeed(
                    trip_name=trip.name,
                    destination=trip.destination,
                    mode="rail",
                    origin=station,
                    destination_code=trip.destination,
                    priority=100 + station_index,
                    notes="Rail/coach path seed; verify via operator or trusted rail seller.",
                )
            )
    return sorted(seeds, key=lambda item: item.priority)


def route_seeds_for_watchlist(watchlist: Watchlist) -> list[RouteSeed]:
    seeds: list[RouteSeed] = []
    for trip in watchlist.watched_trips:
        seeds.extend(route_seeds_for_trip(watchlist, trip))
    return seeds


def destination_airports(destination: str) -> tuple[str, ...]:
    return DESTINATION_AIRPORTS.get(destination.strip().casefold(), (destination[:3].upper(),))


def _flight_notes(origin: str, destination_code: str) -> str:
    if origin == "BRS":
        return f"Primary Cheltenham airport search: Bristol to {destination_code}."
    if origin == "BHX":
        return f"Secondary Cheltenham airport search: Birmingham to {destination_code}."
    return f"Fallback London-area airport search: {origin} to {destination_code}."
