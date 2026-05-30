from __future__ import annotations

from datetime import date
from pathlib import Path

from typer.testing import CliRunner

from eurotour_agent.audit import audit_research_run
from eurotour_agent.calendar import find_free_windows
from eurotour_agent.destinations import draft_watched_trips, suggest_destinations
from eurotour_agent.google_calendar import build_authorization_url as build_google_authorization_url
from eurotour_agent.google_calendar import create_pkce_state as create_google_pkce_state
from eurotour_agent.models import RecommendationDecision
from eurotour_agent.planner import rank_candidate_trips
from eurotour_agent.prices import price_alerts
from eurotour_agent.providers.ticketmaster import _event_from_ticketmaster
from eurotour_agent.research import build_research_run
from eurotour_agent.scheduler import app
from eurotour_agent.spotify import build_authorization_url, create_pkce_state
from eurotour_agent.storage import (
    load_calendar_snapshot,
    load_currency_rates,
    load_manual_findings,
    load_music_taste,
    load_price_history,
    load_research_run,
    load_trip_history,
    load_watchlist,
)


ROOT = Path(__file__).resolve().parents[1]


def test_watchlist_loads() -> None:
    watchlist = load_watchlist(ROOT / "data" / "watchlist.example.yaml")

    assert watchlist.profile.home_city == "Cheltenham"
    assert watchlist.profile.preferred_airports[:2] == ["BRS", "BHX"]
    assert len(watchlist.watched_trips) == 2


def test_trip_history_loads() -> None:
    history = load_trip_history(ROOT / "data" / "trip_history.example.yaml")

    assert len(history.trips) == 4
    assert history.trips[0].destination == "Berlin"
    assert history.trips[0].rating == 4.6


def test_price_history_alerts_on_latest_drop() -> None:
    history = load_price_history(ROOT / "data" / "price_history.example.yaml")

    alerts = price_alerts(history, drop_threshold_percent=10)

    assert len(alerts) == 2
    assert alerts[0].watched_trip == "Berlin long weekend"
    assert alerts[0].is_new_low is True
    assert alerts[0].drop_percent == 20.0
    assert alerts[1].watched_trip == "Amsterdam by rail"
    assert alerts[1].is_new_low is True


def test_research_run_generates_fixture_candidates() -> None:
    watchlist_path = ROOT / "data" / "watchlist.example.yaml"
    watchlist = load_watchlist(watchlist_path)

    research_run = build_research_run(watchlist, watchlist_path=str(watchlist_path))

    assert len(research_run.candidate_trips) == 2
    assert research_run.candidate_trips[0].transport_options
    assert research_run.candidate_trips[0].event_options


def test_trip_history_adds_affinity_and_diversity_signals() -> None:
    watchlist_path = ROOT / "data" / "watchlist.example.yaml"
    findings_path = ROOT / "data" / "manual_findings.example.yaml"
    history_path = ROOT / "data" / "trip_history.example.yaml"
    watchlist = load_watchlist(watchlist_path)
    findings = load_manual_findings(findings_path)
    history = load_trip_history(history_path)

    research_run = build_research_run(
        watchlist,
        watchlist_path=str(watchlist_path),
        manual_findings=findings,
        trip_history=history,
    )
    recommendations = rank_candidate_trips(
        research_run.calendar_windows,
        research_run.candidate_trips,
        trip_history=research_run.trip_history,
    )
    berlin = next(item for item in recommendations if item.trip_name == "Berlin long weekend")

    assert research_run.trip_history is not None
    assert any("prior visit" in reason for reason in berlin.reasons)
    assert any("diversify" in risk for risk in berlin.risks)


def test_destination_suggestions_use_history_without_repeating_it() -> None:
    history = load_trip_history(ROOT / "data" / "trip_history.example.yaml")

    suggestions = suggest_destinations(history, limit=5)

    assert suggestions
    assert all(suggestion.city != "Berlin" for suggestion in suggestions)
    assert any("electronic" in suggestion.matched_tags or "walkable" in suggestion.matched_tags for suggestion in suggestions)


def test_draft_watched_trips_skips_existing_destinations() -> None:
    history = load_trip_history(ROOT / "data" / "trip_history.example.yaml")

    drafted = draft_watched_trips(
        history=history,
        existing_destinations={"Berlin", "Amsterdam"},
        earliest_start=date(2026, 10, 1),
        latest_end=date(2026, 12, 31),
        limit=3,
        budget_limit=1000,
    )

    assert len(drafted) == 3
    assert drafted[0].destination == "Leipzig"
    assert all(trip.destination not in {"Berlin", "Amsterdam"} for trip in drafted)
    assert drafted[0].watch.concerts is True


def test_manual_findings_merge_and_calendar_score() -> None:
    watchlist_path = ROOT / "data" / "watchlist.example.yaml"
    findings_path = ROOT / "data" / "manual_findings.example.yaml"
    watchlist = load_watchlist(watchlist_path)
    findings = load_manual_findings(findings_path)

    research_run = build_research_run(watchlist, watchlist_path=str(watchlist_path), manual_findings=findings)
    berlin = next(trip for trip in research_run.candidate_trips if trip.name == "Berlin long weekend")
    recommendations = rank_candidate_trips(research_run.calendar_windows, research_run.candidate_trips)

    assert berlin.calendar_fit is True
    assert any(option.source == "manual" for option in berlin.transport_options)
    assert recommendations[0].score >= recommendations[-1].score


def test_manual_findings_can_anchor_trip_dates() -> None:
    watchlist_path = ROOT / "data" / "watchlist.example.yaml"
    findings_path = ROOT / "data" / "manual_findings.sample-2026-05-30.yaml"
    watchlist = load_watchlist(watchlist_path)
    findings = load_manual_findings(findings_path)

    research_run = build_research_run(watchlist, watchlist_path=str(watchlist_path), manual_findings=findings)
    berlin = next(trip for trip in research_run.candidate_trips if trip.name == "Berlin long weekend")

    assert berlin.start_date.isoformat() == "2026-07-03"
    assert berlin.end_date.isoformat() == "2026-07-06"


def test_music_taste_boosts_matching_events() -> None:
    watchlist_path = ROOT / "data" / "watchlist.example.yaml"
    findings_path = ROOT / "data" / "manual_findings.sample-2026-05-30.yaml"
    music_taste_path = ROOT / "data" / "music_taste" / "sample.yaml"
    watchlist = load_watchlist(watchlist_path)
    findings = load_manual_findings(findings_path)
    music_taste = load_music_taste(music_taste_path)

    research_run = build_research_run(
        watchlist,
        watchlist_path=str(watchlist_path),
        manual_findings=findings,
        music_taste=music_taste,
    )
    amsterdam = next(trip for trip in research_run.candidate_trips if trip.name == "Amsterdam by rail")
    kevin_morby = next(event for event in amsterdam.event_options if event.artist == "Kevin Morby and Liam Kazar")

    assert kevin_morby.relevance_score >= 0.9
    assert "Spotify taste match" in (kevin_morby.relevance_reason or "")


def test_recommendations_track_incomplete_costs() -> None:
    watchlist_path = ROOT / "data" / "watchlist.example.yaml"
    findings_path = ROOT / "data" / "manual_findings.sample-2026-05-30.yaml"
    watchlist = load_watchlist(watchlist_path)
    findings = load_manual_findings(findings_path)

    research_run = build_research_run(watchlist, watchlist_path=str(watchlist_path), manual_findings=findings)
    berlin = next(item for item in rank_candidate_trips(research_run.calendar_windows, research_run.candidate_trips) if item.trip_name == "Berlin long weekend")

    assert berlin.estimate_complete is False
    assert berlin.decision == RecommendationDecision.RESEARCH_NEEDED
    assert "event" in {category.value for category in berlin.missing_cost_categories}


def test_complete_findings_can_be_ready_to_verify() -> None:
    watchlist_path = ROOT / "data" / "watchlist.example.yaml"
    findings_path = ROOT / "data" / "manual_findings.complete-example.yaml"
    watchlist = load_watchlist(watchlist_path)
    findings = load_manual_findings(findings_path)

    research_run = build_research_run(watchlist, watchlist_path=str(watchlist_path), manual_findings=findings)
    berlin = next(
        item
        for item in rank_candidate_trips(research_run.calendar_windows, research_run.candidate_trips)
        if item.trip_name == "Berlin long weekend"
    )

    assert berlin.estimate_complete is True
    assert berlin.decision == RecommendationDecision.READY_TO_VERIFY


def test_over_budget_trip_is_not_ready_to_verify() -> None:
    watchlist_path = ROOT / "data" / "watchlist.example.yaml"
    findings_path = ROOT / "data" / "manual_findings.complete-example.yaml"
    watchlist = load_watchlist(watchlist_path)
    findings = load_manual_findings(findings_path)
    findings.trips["Berlin long weekend"].cost_components[1].amount = 1000

    research_run = build_research_run(watchlist, watchlist_path=str(watchlist_path), manual_findings=findings)
    berlin = next(
        item
        for item in rank_candidate_trips(research_run.calendar_windows, research_run.candidate_trips)
        if item.trip_name == "Berlin long weekend"
    )

    assert berlin.decision != RecommendationDecision.READY_TO_VERIFY
    assert any("above the trip budget" in risk for risk in berlin.risks)


def test_currency_rates_convert_mixed_trip_costs() -> None:
    watchlist_path = ROOT / "data" / "watchlist.example.yaml"
    findings_path = ROOT / "data" / "manual_findings.sample-2026-05-30.yaml"
    rates_path = ROOT / "data" / "currency_rates.example.yaml"
    watchlist = load_watchlist(watchlist_path)
    findings = load_manual_findings(findings_path)
    rates = load_currency_rates(rates_path)

    research_run = build_research_run(
        watchlist,
        watchlist_path=str(watchlist_path),
        manual_findings=findings,
        currency_rates=rates,
    )
    amsterdam = next(
        item
        for item in rank_candidate_trips(
            research_run.calendar_windows,
            research_run.candidate_trips,
            currency_rates=research_run.currency_rates,
        )
        if item.trip_name == "Amsterdam by rail"
    )

    assert amsterdam.estimated_total_currency == "USD"
    assert amsterdam.estimated_total_amount is not None


def test_calendar_snapshot_finds_free_windows() -> None:
    snapshot = load_calendar_snapshot(ROOT / "data" / "calendar_snapshot.example.yaml")

    windows = find_free_windows(snapshot, min_nights=2, max_nights=5, buffer_hours=2)

    assert windows
    assert all((window.ends_at.date() - window.starts_at.date()).days >= 2 for window in windows)
    assert windows[0].starts_at.date().isoformat() == "2026-07-01"


def test_spotify_auth_url_uses_pkce_and_scopes() -> None:
    pkce_state = create_pkce_state()

    url = build_authorization_url(
        client_id="client-id",
        redirect_uri="http://localhost:8765/callback",
        pkce_state=pkce_state,
    )

    assert "code_challenge_method=S256" in url
    assert "user-top-read" in url
    assert "user-follow-read" in url


def test_google_auth_url_uses_readonly_scope_and_pkce() -> None:
    pkce_state = create_google_pkce_state()

    url = build_google_authorization_url(
        client_id="client-id",
        redirect_uri="http://localhost:8765/google/callback",
        pkce_state=pkce_state,
    )

    assert "code_challenge_method=S256" in url
    assert "calendar.readonly" in url
    assert "access_type=offline" in url


def test_ticketmaster_event_normalization() -> None:
    event = _event_from_ticketmaster(
        {
            "name": "Example Show",
            "url": "https://example.com/tickets",
            "dates": {"start": {"localDate": "2026-07-02"}, "status": {"code": "onsale"}},
            "priceRanges": [{"min": 42.5, "currency": "GBP"}],
            "_embedded": {
                "venues": [{"name": "Example Venue", "city": {"name": "Bristol"}}],
                "attractions": [{"name": "Example Artist"}],
            },
        },
        fallback_city="Bristol",
    )

    assert event.artist == "Example Artist"
    assert event.venue == "Example Venue"
    assert event.estimated_price_currency == "GBP"


def test_report_includes_run_summary() -> None:
    from eurotour_agent.reporting import render_markdown_report

    watchlist_path = ROOT / "data" / "watchlist.example.yaml"
    findings_path = ROOT / "data" / "manual_findings.sample-2026-05-30.yaml"
    rates_path = ROOT / "data" / "currency_rates.example.yaml"
    watchlist = load_watchlist(watchlist_path)
    findings = load_manual_findings(findings_path)
    rates = load_currency_rates(rates_path)
    research_run = build_research_run(
        watchlist,
        watchlist_path=str(watchlist_path),
        manual_findings=findings,
        currency_rates=rates,
    )

    report = render_markdown_report(research_run)

    assert "## Run Summary" in report
    assert "Candidate trips: 2" in report


def test_audit_research_run_flags_incomplete_data() -> None:
    watchlist_path = ROOT / "data" / "watchlist.example.yaml"
    findings_path = ROOT / "data" / "manual_findings.sample-2026-05-30.yaml"
    watchlist = load_watchlist(watchlist_path)
    findings = load_manual_findings(findings_path)
    research_run = build_research_run(watchlist, watchlist_path=str(watchlist_path), manual_findings=findings)

    issues = audit_research_run(research_run)

    assert any("estimate incomplete" in issue for issue in issues)
    assert any("missing ticket price" in issue for issue in issues)


def test_rank_downranks_unverified_fixture_data_to_watch() -> None:
    watchlist_path = ROOT / "data" / "watchlist.example.yaml"
    watchlist = load_watchlist(watchlist_path)
    research_run = build_research_run(watchlist, watchlist_path=str(watchlist_path))

    recommendations = rank_candidate_trips([], research_run.candidate_trips)

    assert recommendations
    assert all(item.decision in {RecommendationDecision.WATCH, RecommendationDecision.IGNORE} for item in recommendations)
    assert any("Calendar fit has not been verified." in item.risks for item in recommendations)


def test_cli_refresh_rank_report(tmp_path: Path) -> None:
    runner = CliRunner()
    run_path = tmp_path / "run.json"
    report_path = tmp_path / "report.md"

    refresh_result = runner.invoke(
        app,
        [
            "refresh-watchlist",
            "--watchlist",
            str(ROOT / "data" / "watchlist.example.yaml"),
            "--findings",
            str(ROOT / "data" / "manual_findings.example.yaml"),
            "--output",
            str(run_path),
        ],
    )
    assert refresh_result.exit_code == 0, refresh_result.output
    assert load_research_run(run_path).candidate_trips

    rank_result = runner.invoke(app, ["rank", "--input", str(run_path)])
    assert rank_result.exit_code == 0, rank_result.output
    assert '"decision"' in rank_result.output

    report_result = runner.invoke(app, ["report", "--input", str(run_path), "--output", str(report_path)])
    assert report_result.exit_code == 0, report_result.output
    assert "EuroTour Agent Report" in report_path.read_text(encoding="utf-8")


def test_cli_refresh_accepts_trip_history(tmp_path: Path) -> None:
    runner = CliRunner()
    run_path = tmp_path / "run.json"

    result = runner.invoke(
        app,
        [
            "refresh-watchlist",
            "--watchlist",
            str(ROOT / "data" / "watchlist.example.yaml"),
            "--findings",
            str(ROOT / "data" / "manual_findings.example.yaml"),
            "--history",
            str(ROOT / "data" / "trip_history.example.yaml"),
            "--output",
            str(run_path),
        ],
    )

    assert result.exit_code == 0, result.output
    research_run = load_research_run(run_path)
    assert research_run.trip_history is not None
    assert len(research_run.trip_history.trips) == 4


def test_cli_history_summary() -> None:
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "history-summary",
            "--history",
            str(ROOT / "data" / "trip_history.example.yaml"),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Trips recorded: 4" in result.output
    assert "Average rating" in result.output


def test_cli_suggest_destinations() -> None:
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "suggest-destinations",
            "--history",
            str(ROOT / "data" / "trip_history.example.yaml"),
            "--limit",
            "3",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "score" in result.output
    assert "Matches prior liked tags" in result.output


def test_cli_draft_watchlist_destinations(tmp_path: Path) -> None:
    runner = CliRunner()
    output_path = tmp_path / "watchlist.suggested.yaml"

    result = runner.invoke(
        app,
        [
            "draft-watchlist-destinations",
            "--watchlist",
            str(ROOT / "data" / "watchlist.example.yaml"),
            "--history",
            str(ROOT / "data" / "trip_history.example.yaml"),
            "--output",
            str(output_path),
            "--earliest-start",
            "2026-10-01",
            "--latest-end",
            "2026-12-31",
            "--limit",
            "2",
        ],
    )

    assert result.exit_code == 0, result.output
    watchlist = load_watchlist(output_path)
    assert len(watchlist.watched_trips) == 4
    assert any(trip.destination == "Leipzig" for trip in watchlist.watched_trips)


def test_cli_find_free_windows(tmp_path: Path) -> None:
    runner = CliRunner()
    output_path = tmp_path / "windows.json"

    result = runner.invoke(
        app,
        [
            "find-free-windows",
            "--calendar",
            str(ROOT / "data" / "calendar_snapshot.example.yaml"),
            "--output",
            str(output_path),
            "--min-nights",
            "2",
            "--max-nights",
            "5",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "starts_at" in output_path.read_text(encoding="utf-8")


def test_cli_attach_events(tmp_path: Path) -> None:
    runner = CliRunner()
    events_path = tmp_path / "events.yaml"
    output_path = tmp_path / "findings.yaml"
    events_path.write_text(
        """
event_options:
  - artist: Example Artist
    city: Berlin
    event_date: "2026-07-02"
    source: ticketmaster
    relevance_score: 0.5
""",
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "attach-events",
            "Berlin long weekend",
            "--events",
            str(events_path),
            "--output",
            str(output_path),
            "--start-date",
            "2026-07-01",
            "--end-date",
            "2026-07-04",
            "--calendar-fit",
        ],
    )

    assert result.exit_code == 0, result.output
    output_text = output_path.read_text(encoding="utf-8")
    assert "Berlin long weekend" in output_text
    assert "Example Artist" in output_text


def test_cli_attach_transport(tmp_path: Path) -> None:
    runner = CliRunner()
    transport_path = tmp_path / "transport.yaml"
    output_path = tmp_path / "findings.yaml"
    transport_path.write_text(
        """
transport_options:
  - mode: flight
    origin: BRS
    destination: BER
    source: manual
    price_amount: 120
    price_currency: GBP
    booking_confidence: 0.6
""",
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "attach-transport",
            "Berlin long weekend",
            "--transport",
            str(transport_path),
            "--output",
            str(output_path),
            "--start-date",
            "2026-07-01",
            "--end-date",
            "2026-07-04",
        ],
    )

    assert result.exit_code == 0, result.output
    output_text = output_path.read_text(encoding="utf-8")
    assert "transport_options" in output_text
    assert "BRS" in output_text


def test_cli_attach_accommodation(tmp_path: Path) -> None:
    runner = CliRunner()
    accommodation_path = tmp_path / "accommodation.yaml"
    output_path = tmp_path / "findings.yaml"
    accommodation_path.write_text(
        """
accommodation_options:
  - name: Example Hotel
    city: Berlin
    check_in: "2026-07-01"
    check_out: "2026-07-04"
    total_price_amount: 360
    price_currency: GBP
    booking_confidence: 0.5
""",
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "attach-accommodation",
            "Berlin long weekend",
            "--accommodation",
            str(accommodation_path),
            "--output",
            str(output_path),
        ],
    )

    assert result.exit_code == 0, result.output
    output_text = output_path.read_text(encoding="utf-8")
    assert "accommodation_options" in output_text
    assert "Example Hotel" in output_text


def test_cli_merge_findings(tmp_path: Path) -> None:
    runner = CliRunner()
    events_path = tmp_path / "events_findings.yaml"
    transport_path = tmp_path / "transport_findings.yaml"
    output_path = tmp_path / "merged.yaml"
    events_path.write_text(
        """
trips:
  Berlin long weekend:
    event_options:
      - artist: Example Artist
        city: Berlin
        event_date: "2026-07-02"
""",
        encoding="utf-8",
    )
    transport_path.write_text(
        """
trips:
  Berlin long weekend:
    transport_options:
      - mode: flight
        origin: BRS
        destination: BER
""",
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "merge-findings",
            str(events_path),
            str(transport_path),
            "--output",
            str(output_path),
        ],
    )

    assert result.exit_code == 0, result.output
    output_text = output_path.read_text(encoding="utf-8")
    assert "event_options" in output_text
    assert "transport_options" in output_text


def test_cli_research_brief(tmp_path: Path) -> None:
    runner = CliRunner()
    output_path = tmp_path / "brief.md"

    result = runner.invoke(
        app,
        [
            "research-brief",
            "Berlin long weekend",
            "--output",
            str(output_path),
        ],
    )

    assert result.exit_code == 0, result.output
    output_text = output_path.read_text(encoding="utf-8")
    assert "Research Brief: Berlin long weekend" in output_text
    assert "BRS" in output_text
    assert "Ticketmaster" in output_text


def test_cli_create_option_templates(tmp_path: Path) -> None:
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "create-option-templates",
            "Berlin long weekend",
            "--output-dir",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0, result.output
    assert (tmp_path / "berlin-long-weekend.transport.yaml").exists()
    assert (tmp_path / "berlin-long-weekend.accommodation.yaml").exists()
    assert (tmp_path / "berlin-long-weekend.events.yaml").exists()


def test_cli_trip_pack(tmp_path: Path) -> None:
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "trip-pack",
            "Berlin long weekend",
            "--output-dir",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0, result.output
    assert (tmp_path / "berlin-long-weekend.brief.md").exists()
    assert (tmp_path / "berlin-long-weekend.transport.yaml").exists()
    assert (tmp_path / "berlin-long-weekend.accommodation.yaml").exists()
    assert (tmp_path / "berlin-long-weekend.events.yaml").exists()


def test_cli_validate_file(tmp_path: Path) -> None:
    runner = CliRunner()
    transport_path = tmp_path / "transport.yaml"
    transport_path.write_text(
        """
transport_options:
  - mode: flight
    origin: BRS
    destination: BER
""",
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "validate-file",
            str(transport_path),
            "--kind",
            "transport",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "valid transport" in result.output


def test_cli_price_alerts(tmp_path: Path) -> None:
    runner = CliRunner()
    output_path = tmp_path / "price_alerts.json"

    result = runner.invoke(
        app,
        [
            "price-alerts",
            "--history",
            str(ROOT / "data" / "price_history.example.yaml"),
            "--output",
            str(output_path),
            "--drop-threshold-percent",
            "10",
        ],
    )

    assert result.exit_code == 0, result.output
    output_text = output_path.read_text(encoding="utf-8")
    assert "Berlin long weekend" in output_text
    assert "drop_percent" in output_text


def test_cli_audit_run_flags_sample(tmp_path: Path) -> None:
    runner = CliRunner()
    run_path = tmp_path / "run.json"
    refresh_result = runner.invoke(
        app,
        [
            "refresh-watchlist",
            "--findings",
            str(ROOT / "data" / "manual_findings.sample-2026-05-30.yaml"),
            "--output",
            str(run_path),
        ],
    )
    assert refresh_result.exit_code == 0, refresh_result.output

    result = runner.invoke(app, ["audit-run", "--input", str(run_path)])

    assert result.exit_code == 1
    assert "ISSUE:" in result.output
