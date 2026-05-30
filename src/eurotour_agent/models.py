from __future__ import annotations

from datetime import UTC, date, datetime
from enum import StrEnum

from pydantic import BaseModel, Field, model_validator


class TripStatus(StrEnum):
    WATCHING = "watching"
    SHORTLISTED = "shortlisted"
    PLANNED = "planned"
    ARCHIVED = "archived"


class RecommendationDecision(StrEnum):
    READY_TO_VERIFY = "ready_to_verify"
    WATCH = "watch"
    RESEARCH_NEEDED = "research_needed"
    IGNORE = "ignore"


class CostCategory(StrEnum):
    TRANSPORT = "transport"
    ACCOMMODATION = "accommodation"
    EVENT = "event"
    LOCAL_TRANSIT = "local_transit"
    FOOD_DRINK = "food_drink"
    BUFFER = "buffer"
    OTHER = "other"


class WatchFlags(BaseModel):
    flights: bool = True
    trains: bool = True
    concerts: bool = True


class PreferenceProfile(BaseModel):
    home_city: str
    preferred_airports: list[str] = Field(default_factory=list)
    preferred_stations: list[str] = Field(default_factory=list)
    default_currency: str = "USD"
    max_trip_budget: float | None = None
    pace: str | None = None


class MusicPreferences(BaseModel):
    priority_artists: list[str] = Field(default_factory=list)
    genres: list[str] = Field(default_factory=list)
    discovery_notes: str | None = None


class MusicTasteArtist(BaseModel):
    name: str
    source: str = "manual"
    spotify_id: str | None = None
    genres: list[str] = Field(default_factory=list)
    popularity: int | None = Field(default=None, ge=0, le=100)
    weight: float = Field(default=0.5, ge=0.0, le=1.0)


class MusicTasteProfile(BaseModel):
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    source: str = "manual"
    artists: list[MusicTasteArtist] = Field(default_factory=list)
    genres: list[str] = Field(default_factory=list)

    def priority_artist_names(self, limit: int = 50) -> list[str]:
        artists = sorted(self.artists, key=lambda item: item.weight, reverse=True)
        return [artist.name for artist in artists[:limit]]


class PastTrip(BaseModel):
    destination: str
    country: str | None = None
    started_on: date
    ended_on: date
    rating: float | None = Field(default=None, ge=0.0, le=5.0)
    music_rating: float | None = Field(default=None, ge=0.0, le=5.0)
    food_rating: float | None = Field(default=None, ge=0.0, le=5.0)
    lodging_rating: float | None = Field(default=None, ge=0.0, le=5.0)
    transport_rating: float | None = Field(default=None, ge=0.0, le=5.0)
    pace_rating: float | None = Field(default=None, ge=0.0, le=5.0)
    would_repeat: bool | None = None
    tags: list[str] = Field(default_factory=list)
    liked: list[str] = Field(default_factory=list)
    disliked: list[str] = Field(default_factory=list)
    notes: str | None = None

    @model_validator(mode="after")
    def validate_trip_dates(self) -> "PastTrip":
        if self.ended_on < self.started_on:
            raise ValueError("ended_on must be on or after started_on")
        return self


class TripHistory(BaseModel):
    trips: list[PastTrip] = Field(default_factory=list)


class WatchedTrip(BaseModel):
    name: str
    destination: str
    earliest_start: date
    latest_end: date
    nights_min: int = Field(default=2, ge=1)
    nights_max: int = Field(default=5, ge=1)
    budget_limit: float | None = None
    watch: WatchFlags = Field(default_factory=WatchFlags)
    notes: str | None = None

    @model_validator(mode="after")
    def validate_trip_window(self) -> "WatchedTrip":
        if self.latest_end < self.earliest_start:
            raise ValueError("latest_end must be on or after earliest_start")
        if self.nights_max < self.nights_min:
            raise ValueError("nights_max must be greater than or equal to nights_min")
        return self


class AlertRules(BaseModel):
    price_drop_threshold_percent: float = Field(default=15.0, ge=0)
    max_total_travel_time_hours: float | None = Field(default=8.0, gt=0)
    require_calendar_fit: bool = True


class Watchlist(BaseModel):
    profile: PreferenceProfile
    music: MusicPreferences = Field(default_factory=MusicPreferences)
    watched_trips: list[WatchedTrip] = Field(default_factory=list)
    alerts: AlertRules = Field(default_factory=AlertRules)


class CalendarWindow(BaseModel):
    starts_at: datetime
    ends_at: datetime
    label: str | None = None

    @model_validator(mode="after")
    def validate_window(self) -> "CalendarWindow":
        if self.ends_at <= self.starts_at:
            raise ValueError("ends_at must be after starts_at")
        return self


class BusyCalendarEvent(BaseModel):
    starts_at: datetime
    ends_at: datetime
    title: str | None = None
    source: str = "manual"
    transparent: bool = False

    @model_validator(mode="after")
    def validate_event(self) -> "BusyCalendarEvent":
        if self.ends_at <= self.starts_at:
            raise ValueError("ends_at must be after starts_at")
        return self


class CalendarSnapshot(BaseModel):
    timezone: str = "Europe/London"
    range_start: datetime
    range_end: datetime
    busy_events: list[BusyCalendarEvent] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_range(self) -> "CalendarSnapshot":
        if self.range_end <= self.range_start:
            raise ValueError("range_end must be after range_start")
        return self


class TransportOption(BaseModel):
    mode: str
    origin: str
    destination: str
    source: str = "manual"
    provider: str | None = None
    departs_at: datetime | None = None
    arrives_at: datetime | None = None
    price_amount: float | None = None
    price_currency: str = "USD"
    total_travel_time_hours: float | None = None
    baggage_included: bool | None = None
    booking_confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    booking_url: str | None = None
    notes: str | None = None
    observed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class EventOption(BaseModel):
    artist: str
    city: str
    source: str = "manual"
    venue: str | None = None
    event_date: date
    ticket_url: str | None = None
    ticket_status: str | None = None
    estimated_price_amount: float | None = None
    estimated_price_currency: str = "USD"
    relevance_score: float = Field(default=0.0, ge=0.0, le=1.0)
    relevance_reason: str | None = None


class AccommodationOption(BaseModel):
    name: str
    city: str
    source: str = "manual"
    area: str | None = None
    check_in: date
    check_out: date
    nightly_price_amount: float | None = None
    total_price_amount: float | None = None
    price_currency: str = "USD"
    refundable: bool | None = None
    booking_confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    booking_url: str | None = None
    notes: str | None = None

    @model_validator(mode="after")
    def validate_stay_dates(self) -> "AccommodationOption":
        if self.check_out <= self.check_in:
            raise ValueError("check_out must be after check_in")
        return self


class CostComponent(BaseModel):
    category: CostCategory
    label: str
    source: str = "manual"
    amount: float | None = None
    currency: str = "USD"
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    notes: str | None = None


class PriceObservation(BaseModel):
    watched_trip: str
    category: CostCategory
    label: str
    source: str = "manual"
    amount: float = Field(ge=0)
    currency: str = "USD"
    observed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    url: str | None = None
    notes: str | None = None


class PriceHistory(BaseModel):
    observations: list[PriceObservation] = Field(default_factory=list)


class PriceAlert(BaseModel):
    watched_trip: str
    category: CostCategory
    label: str
    current_amount: float
    previous_low_amount: float | None = None
    currency: str
    drop_percent: float | None = None
    is_new_low: bool = False
    observed_at: datetime
    source: str
    url: str | None = None
    reason: str


class CurrencyRate(BaseModel):
    from_currency: str
    to_currency: str
    rate: float = Field(gt=0)
    source: str = "manual"
    observed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class CurrencyRateSnapshot(BaseModel):
    base_currency: str = "USD"
    rates: list[CurrencyRate] = Field(default_factory=list)

    def convert(self, amount: float, from_currency: str, to_currency: str) -> float | None:
        if from_currency == to_currency:
            return amount
        for rate in self.rates:
            if rate.from_currency == from_currency and rate.to_currency == to_currency:
                return amount * rate.rate
            if rate.from_currency == to_currency and rate.to_currency == from_currency:
                return amount / rate.rate
        return None


class CandidateTrip(BaseModel):
    name: str
    destination: str
    start_date: date
    end_date: date
    status: TripStatus = TripStatus.WATCHING
    reason: str
    budget_limit_amount: float | None = None
    budget_currency: str = "USD"
    transport_options: list[TransportOption] = Field(default_factory=list)
    event_options: list[EventOption] = Field(default_factory=list)
    accommodation_options: list[AccommodationOption] = Field(default_factory=list)
    cost_components: list[CostComponent] = Field(default_factory=list)
    calendar_fit: bool | None = None
    source_notes: list[str] = Field(default_factory=list)


class ManualTripFindings(BaseModel):
    start_date: date | None = None
    end_date: date | None = None
    calendar_fit: bool | None = None
    transport_options: list[TransportOption] = Field(default_factory=list)
    event_options: list[EventOption] = Field(default_factory=list)
    accommodation_options: list[AccommodationOption] = Field(default_factory=list)
    cost_components: list[CostComponent] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_manual_dates(self) -> "ManualTripFindings":
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        return self


class ManualFindings(BaseModel):
    calendar_windows: list[CalendarWindow] = Field(default_factory=list)
    trips: dict[str, ManualTripFindings] = Field(default_factory=dict)


class ResearchRun(BaseModel):
    generated_at: datetime
    mode: str
    watchlist_path: str
    calendar_windows: list[CalendarWindow] = Field(default_factory=list)
    currency_rates: CurrencyRateSnapshot | None = None
    trip_history: TripHistory | None = None
    candidate_trips: list[CandidateTrip] = Field(default_factory=list)
    source_notes: list[str] = Field(default_factory=list)


class Recommendation(BaseModel):
    trip_name: str
    destination: str
    decision: RecommendationDecision
    title: str
    summary: str
    score: float = Field(ge=0.0, le=1.0)
    estimated_total_amount: float | None = None
    estimated_total_currency: str = "USD"
    estimate_complete: bool = False
    missing_cost_categories: list[CostCategory] = Field(default_factory=list)
    cost_breakdown: list[CostComponent] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)
