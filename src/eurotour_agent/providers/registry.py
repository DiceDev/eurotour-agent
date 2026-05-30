from __future__ import annotations

from dataclasses import dataclass

from eurotour_agent.config import Settings


@dataclass(frozen=True)
class ProviderRecord:
    name: str
    domain: str
    role: str
    docs_url: str
    required_env: tuple[str, ...] = ()
    phase: str = "manual"
    reliability_score: float = 0.5
    integration_notes: str = ""


@dataclass(frozen=True)
class ProviderReadiness:
    provider: ProviderRecord
    configured: bool
    missing_env: tuple[str, ...]


PROVIDERS: tuple[ProviderRecord, ...] = (
    ProviderRecord(
        name="Google Calendar",
        domain="calendar",
        role="Read busy time and infer free travel windows.",
        docs_url="https://developers.google.com/calendar/api/v3/reference/freebusy/query",
        required_env=("GOOGLE_CLIENT_ID",),
        phase="implemented",
        reliability_score=0.95,
        integration_notes="OAuth PKCE flow exists; read-only calendar access is enough for free/busy checks.",
    ),
    ProviderRecord(
        name="Spotify",
        domain="music",
        role="Import top and followed artists to drive concert searches.",
        docs_url="https://developer.spotify.com/documentation/web-api/reference/get-users-top-artists-and-tracks",
        required_env=("SPOTIFY_CLIENT_ID",),
        phase="implemented",
        reliability_score=0.9,
        integration_notes="OAuth PKCE flow exists; use user-top-read and user-follow-read.",
    ),
    ProviderRecord(
        name="Ticketmaster Discovery API",
        domain="events",
        role="Find public event inventory by city/date/artist.",
        docs_url="https://developer.ticketmaster.com/products-and-docs/apis/discovery-api/v2/",
        required_env=("TICKETMASTER_API_KEY",),
        phase="implemented",
        reliability_score=0.82,
        integration_notes="Good first live event provider; supplement with venue calendars for smaller acts.",
    ),
    ProviderRecord(
        name="Amadeus Flight Offers",
        domain="flights",
        role="Search and price flight offers from preferred airports.",
        docs_url="https://developers.amadeus.com/self-service/apis-docs/guides/developer-guides/resources/flights/",
        required_env=("AMADEUS_CLIENT_ID", "AMADEUS_CLIENT_SECRET"),
        phase="next",
        reliability_score=0.78,
        integration_notes="Use Flight Offers Search for options and Flight Offers Price before treating fares as current.",
    ),
    ProviderRecord(
        name="Amadeus Hotel Search",
        domain="accommodation",
        role="Find hotel IDs and check availability/prices.",
        docs_url="https://developers.amadeus.com/self-service/apis-docs/guides/developer-guides/resources/hotels/",
        required_env=("AMADEUS_CLIENT_ID", "AMADEUS_CLIENT_SECRET"),
        phase="next",
        reliability_score=0.74,
        integration_notes="Useful for availability snapshots; still verify refundable terms on primary booking source.",
    ),
    ProviderRecord(
        name="National Rail Darwin",
        domain="rail",
        role="Official GB real-time running data.",
        docs_url="https://www.nationalrail.co.uk/developers/darwin-data-feeds/",
        phase="research",
        reliability_score=0.86,
        integration_notes="Good for live running and disruption, not a fare shopping API.",
    ),
    ProviderRecord(
        name="TransportAPI",
        domain="ground_transport",
        role="Managed UK rail, bus, and multimodal transport data.",
        docs_url="https://www.transportapi.com/",
        required_env=("TRANSPORTAPI_APP_ID", "TRANSPORTAPI_APP_KEY"),
        phase="candidate",
        reliability_score=0.72,
        integration_notes="Good Cheltenham-area local transport candidate if pricing and terms fit personal use.",
    ),
    ProviderRecord(
        name="Trainline Partner/Affiliate",
        domain="rail",
        role="Rail and coach retail/affiliate paths.",
        docs_url="https://www.thetrainline.com/about-us/affiliates",
        phase="manual",
        reliability_score=0.68,
        integration_notes="Partner API appears commercial/approval-based; use manual links until access is justified.",
    ),
    ProviderRecord(
        name="Bandsintown/Songkick/DICE/Venues",
        domain="events",
        role="Catch smaller and non-Ticketmaster music events.",
        docs_url="https://artists.bandsintown.com/support/bandsintown-api",
        phase="manual",
        reliability_score=0.62,
        integration_notes="Treat as secondary discovery/manual verification unless API access terms are confirmed.",
    ),
)

SOURCE_RELIABILITY = {
    "google_calendar": 0.95,
    "spotify": 0.9,
    "ticketmaster": 0.82,
    "amadeus": 0.78,
    "national_rail": 0.86,
    "transportapi": 0.72,
    "manual": 0.55,
    "fixture": 0.25,
}


def provider_readiness(settings: Settings) -> list[ProviderReadiness]:
    env_values = {
        "GOOGLE_CLIENT_ID": settings.google_client_id,
        "SPOTIFY_CLIENT_ID": settings.spotify_client_id,
        "TICKETMASTER_API_KEY": settings.ticketmaster_api_key,
        "AMADEUS_CLIENT_ID": settings.amadeus_client_id,
        "AMADEUS_CLIENT_SECRET": settings.amadeus_client_secret,
        "TRANSPORTAPI_APP_ID": settings.transportapi_app_id,
        "TRANSPORTAPI_APP_KEY": settings.transportapi_app_key,
    }
    readiness: list[ProviderReadiness] = []
    for provider in PROVIDERS:
        missing = tuple(env for env in provider.required_env if not env_values.get(env))
        readiness.append(
            ProviderReadiness(
                provider=provider,
                configured=not missing,
                missing_env=missing,
            )
        )
    return readiness


def provider_readiness_payload(settings: Settings) -> list[dict]:
    return [
        {
            "name": item.provider.name,
            "domain": item.provider.domain,
            "phase": item.provider.phase,
            "configured": item.configured,
            "missing_env": list(item.missing_env),
            "reliability_score": item.provider.reliability_score,
            "docs_url": item.provider.docs_url,
            "role": item.provider.role,
            "integration_notes": item.provider.integration_notes,
        }
        for item in provider_readiness(settings)
    ]


def render_provider_readiness(settings: Settings) -> str:
    lines = ["# Provider Readiness", ""]
    for item in provider_readiness(settings):
        status = "configured" if item.configured else "missing " + ", ".join(item.missing_env)
        lines.append(f"- {item.provider.name} ({item.provider.domain}, {item.provider.phase}): {status}")
        lines.append(f"  Reliability: {item.provider.reliability_score:.2f}. {item.provider.integration_notes}")
    lines.append("")
    return "\n".join(lines)


def source_reliability(source: str | None) -> float:
    if not source:
        return 0.5
    normalized = source.strip().casefold().replace("-", "_").replace(" ", "_")
    for key, score in SOURCE_RELIABILITY.items():
        if key in normalized:
            return score
    return 0.5
