from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from pydantic import ValidationError
import typer

from .audit import audit_research_run
from .briefing import accommodation_template, events_template, render_research_brief, transport_template
from .calendar import find_free_windows
from .config import load_settings
from .destinations import draft_watched_trips, suggest_destinations
from .google_calendar import (
    build_authorization_url as build_google_authorization_url,
    create_pkce_state as create_google_pkce_state,
    exchange_code_for_token as exchange_google_code_for_token,
    get_valid_access_token as get_valid_google_access_token,
    import_freebusy_snapshot,
    load_token as load_google_token,
    refresh_access_token as refresh_google_access_token,
    write_token as write_google_token,
)
from .history import summarize_history
from .models import ManualFindings, ManualTripFindings
from .monitoring import render_monitoring_brief
from .planner import rank_candidate_trips
from .prices import price_alerts
from .providers.ticketmaster import search_music_events
from .reporting import render_markdown_report
from .research import build_research_run
from .spotify import (
    build_authorization_url,
    create_pkce_state,
    exchange_code_for_token,
    get_valid_access_token as get_valid_spotify_access_token,
    import_music_taste,
    load_token,
    refresh_access_token,
    write_token,
)
from .storage import (
    load_accommodation_options,
    load_calendar_snapshot,
    load_currency_rates,
    load_event_options,
    load_manual_findings,
    load_music_taste,
    load_price_history,
    load_research_run,
    load_transport_options,
    load_trip_history,
    load_watchlist,
    write_model,
    write_yaml,
)

app = typer.Typer(help="Run EuroTour Agent checks.")


@app.command()
def run(dry_run: bool = typer.Option(True, help="Preview checks without calling external providers.")) -> None:
    settings = load_settings()
    typer.echo(f"EuroTour Agent run started at {datetime.now(UTC).isoformat()}")
    typer.echo(f"Calendar: {settings.google_calendar_id}")
    typer.echo(f"AI model configured: {settings.openai_model}")
    typer.echo(f"AI monthly budget cap: ${settings.openai_monthly_budget_usd:.2f}")

    if dry_run:
        typer.echo("Dry run: provider calls skipped.")
        recommendations = rank_candidate_trips(calendar_windows=[], candidate_trips=[])
        typer.echo(f"Recommendations generated: {len(recommendations)}")
        return

    typer.echo("Live provider execution is not implemented yet.")


@app.command("refresh-watchlist")
def refresh_watchlist(
    watchlist: Path = typer.Option(Path("data/watchlist.example.yaml"), help="Watchlist YAML path."),
    output: Path = typer.Option(Path("runs/latest/research_run.json"), help="Research run JSON output path."),
    findings: Path | None = typer.Option(None, help="Optional manual findings YAML path."),
    music_taste: Path | None = typer.Option(None, help="Optional music taste YAML path."),
    rates: Path | None = typer.Option(None, help="Optional currency rates YAML path."),
    history: Path | None = typer.Option(None, help="Optional prior trip history YAML path."),
    dry_run: bool = typer.Option(True, help="Use deterministic local fixtures instead of live provider calls."),
) -> None:
    watchlist_model = load_watchlist(watchlist)
    manual_findings = load_manual_findings(findings) if findings else None
    music_taste_model = load_music_taste(music_taste) if music_taste else None
    currency_rates = load_currency_rates(rates) if rates else None
    trip_history = load_trip_history(history) if history else None
    research_run = build_research_run(
        watchlist_model,
        watchlist_path=str(watchlist),
        dry_run=dry_run,
        manual_findings=manual_findings,
        music_taste=music_taste_model,
        currency_rates=currency_rates,
        trip_history=trip_history,
    )
    write_model(output, research_run)
    typer.echo(f"Wrote {len(research_run.candidate_trips)} candidate trip(s) to {output}")


@app.command("refresh-trip")
def refresh_trip(
    trip_name: str = typer.Argument(..., help="Watched trip name to refresh."),
    watchlist: Path = typer.Option(Path("data/watchlist.example.yaml"), help="Watchlist YAML path."),
    output: Path = typer.Option(Path("runs/latest/research_run.json"), help="Research run JSON output path."),
    findings: Path | None = typer.Option(None, help="Optional manual findings YAML path."),
    music_taste: Path | None = typer.Option(None, help="Optional music taste YAML path."),
    rates: Path | None = typer.Option(None, help="Optional currency rates YAML path."),
    history: Path | None = typer.Option(None, help="Optional prior trip history YAML path."),
    dry_run: bool = typer.Option(True, help="Use deterministic local fixtures instead of live provider calls."),
) -> None:
    watchlist_model = load_watchlist(watchlist)
    manual_findings = load_manual_findings(findings) if findings else None
    music_taste_model = load_music_taste(music_taste) if music_taste else None
    currency_rates = load_currency_rates(rates) if rates else None
    trip_history = load_trip_history(history) if history else None
    research_run = build_research_run(
        watchlist_model,
        watchlist_path=str(watchlist),
        trip_name=trip_name,
        dry_run=dry_run,
        manual_findings=manual_findings,
        music_taste=music_taste_model,
        currency_rates=currency_rates,
        trip_history=trip_history,
    )
    if not research_run.candidate_trips:
        raise typer.BadParameter(f"No watched trip named {trip_name!r} found in {watchlist}")
    write_model(output, research_run)
    typer.echo(f"Wrote {len(research_run.candidate_trips)} candidate trip(s) to {output}")


@app.command("daily-brief-run")
def daily_brief_run(
    watchlist: Path = typer.Option(Path("data/watchlist.example.yaml"), help="Watchlist YAML path."),
    output_dir: Path = typer.Option(Path("runs/latest"), help="Directory for run outputs."),
    findings: Path | None = typer.Option(None, help="Optional manual findings YAML path."),
    music_taste: Path | None = typer.Option(None, help="Optional music taste YAML path."),
    rates: Path | None = typer.Option(None, help="Optional currency rates YAML path."),
    history: Path | None = typer.Option(None, help="Optional prior trip history YAML path."),
    prices: Path | None = typer.Option(None, help="Optional price history YAML path."),
    drop_threshold_percent: float = typer.Option(10.0, help="Price drop alert threshold."),
    dry_run: bool = typer.Option(True, help="Use deterministic local fixtures instead of live provider calls."),
) -> None:
    watchlist_model = load_watchlist(watchlist)
    manual_findings = load_manual_findings(findings) if findings else None
    music_taste_model = load_music_taste(music_taste) if music_taste else None
    currency_rates = load_currency_rates(rates) if rates else None
    trip_history = load_trip_history(history) if history else None
    price_history = load_price_history(prices) if prices else None
    research_run = build_research_run(
        watchlist_model,
        watchlist_path=str(watchlist),
        dry_run=dry_run,
        manual_findings=manual_findings,
        music_taste=music_taste_model,
        currency_rates=currency_rates,
        trip_history=trip_history,
    )
    recommendations = rank_candidate_trips(
        calendar_windows=research_run.calendar_windows,
        candidate_trips=research_run.candidate_trips,
        currency_rates=research_run.currency_rates,
        trip_history=research_run.trip_history,
    )
    alerts = price_alerts(price_history, drop_threshold_percent=drop_threshold_percent) if price_history else []

    output_dir.mkdir(parents=True, exist_ok=True)
    write_model(output_dir / "research_run.json", research_run)
    (output_dir / "recommendations.json").write_text(
        json.dumps([recommendation.model_dump(mode="json") for recommendation in recommendations], indent=2) + "\n",
        encoding="utf-8",
    )
    (output_dir / "price_alerts.json").write_text(
        json.dumps([alert.model_dump(mode="json") for alert in alerts], indent=2) + "\n",
        encoding="utf-8",
    )
    (output_dir / "report.md").write_text(render_markdown_report(research_run), encoding="utf-8")
    (output_dir / "monitoring_brief.md").write_text(
        render_monitoring_brief(
            research_run=research_run,
            price_history=price_history,
            drop_threshold_percent=drop_threshold_percent,
        ),
        encoding="utf-8",
    )
    typer.echo(
        f"Wrote daily brief run to {output_dir}: "
        f"{len(recommendations)} recommendation(s), {len(alerts)} price alert(s)."
    )


@app.command("rank")
def rank(
    input_path: Path = typer.Option(Path("runs/latest/research_run.json"), "--input", help="Research run JSON input."),
    output: Path | None = typer.Option(None, help="Optional recommendations JSON output path."),
) -> None:
    research_run = load_research_run(input_path)
    recommendations = rank_candidate_trips(
        calendar_windows=research_run.calendar_windows,
        candidate_trips=research_run.candidate_trips,
        currency_rates=research_run.currency_rates,
        trip_history=research_run.trip_history,
    )
    payload = [recommendation.model_dump(mode="json") for recommendation in recommendations]

    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        typer.echo(f"Wrote {len(recommendations)} recommendation(s) to {output}")
        return

    typer.echo(json.dumps(payload, indent=2))


@app.command("report")
def report(
    input_path: Path = typer.Option(Path("runs/latest/research_run.json"), "--input", help="Research run JSON input."),
    output: Path = typer.Option(Path("runs/latest/report.md"), help="Markdown report output path."),
) -> None:
    research_run = load_research_run(input_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_markdown_report(research_run), encoding="utf-8")
    typer.echo(f"Wrote report to {output}")


@app.command("audit-run")
def audit_run(
    input_path: Path = typer.Option(Path("runs/latest/research_run.json"), "--input", help="Research run JSON input."),
    stale_after_days: int = typer.Option(7, help="Mark timestamped options stale after this many days."),
) -> None:
    research_run = load_research_run(input_path)
    issues = audit_research_run(research_run, stale_after_days=stale_after_days)
    if not issues:
        typer.echo("OK: no audit issues found")
        return
    for issue in issues:
        typer.echo(f"ISSUE: {issue}")
    raise typer.Exit(code=1)


@app.command("find-free-windows")
def find_free_windows_command(
    calendar: Path = typer.Option(Path("data/calendar_snapshot.example.yaml"), help="Calendar snapshot YAML path."),
    output: Path = typer.Option(Path("runs/latest/calendar_windows.json"), help="Free calendar windows JSON output path."),
    min_nights: int = typer.Option(2, help="Minimum nights required for a trip window."),
    max_nights: int | None = typer.Option(5, help="Maximum nights to return per window."),
    buffer_hours: float = typer.Option(2.0, help="Buffer around busy events."),
) -> None:
    snapshot = load_calendar_snapshot(calendar)
    windows = find_free_windows(
        snapshot=snapshot,
        min_nights=min_nights,
        max_nights=max_nights,
        buffer_hours=buffer_hours,
    )
    payload = [window.model_dump(mode="json") for window in windows]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    typer.echo(f"Wrote {len(windows)} free window(s) to {output}")


@app.command("doctor")
def doctor() -> None:
    checks = [
        ("watchlist example", Path("data/watchlist.example.yaml").exists()),
        ("manual findings example", Path("data/manual_findings.example.yaml").exists()),
        ("calendar snapshot example", Path("data/calendar_snapshot.example.yaml").exists()),
        ("runs directory", Path("runs").exists()),
    ]
    settings = load_settings()
    optional = [
        ("Spotify client id", bool(settings.spotify_client_id)),
        ("Google client id", bool(settings.google_client_id)),
        ("Ticketmaster API key", bool(settings.ticketmaster_api_key)),
    ]
    for label, ok in checks:
        typer.echo(f"{'OK' if ok else 'MISSING'}: {label}")
    typer.echo(f"{'OK' if Path('local').exists() else 'OPTIONAL'}: local directory")
    for label, ok in optional:
        typer.echo(f"{'CONFIGURED' if ok else 'OPTIONAL'}: {label}")


@app.command("validate-file")
def validate_file(
    path: Path = typer.Argument(..., help="File to validate."),
    kind: str = typer.Option(
        "findings",
        help="One of: watchlist, findings, calendar, music-taste, rates, history, price-history, events, transport, accommodation, research-run.",
    ),
) -> None:
    validators = {
        "watchlist": load_watchlist,
        "findings": load_manual_findings,
        "calendar": load_calendar_snapshot,
        "music-taste": load_music_taste,
        "rates": load_currency_rates,
        "history": load_trip_history,
        "price-history": load_price_history,
        "events": load_event_options,
        "transport": load_transport_options,
        "accommodation": load_accommodation_options,
        "research-run": load_research_run,
    }
    validator = validators.get(kind)
    if validator is None:
        raise typer.BadParameter(f"Unknown kind {kind!r}.")
    try:
        validator(path)
    except (ValidationError, ValueError, KeyError, TypeError) as exc:
        raise typer.BadParameter(f"{path} is not valid {kind}: {exc}") from exc
    typer.echo(f"OK: {path} is valid {kind}")


@app.command("price-alerts")
def price_alerts_command(
    history: Path = typer.Option(Path("data/price_history.example.yaml"), help="Price history YAML path."),
    output: Path | None = typer.Option(None, help="Optional price alerts JSON output path."),
    drop_threshold_percent: float = typer.Option(10.0, help="Alert when latest price drops by at least this percent."),
) -> None:
    price_history = load_price_history(history)
    alerts = price_alerts(price_history, drop_threshold_percent=drop_threshold_percent)
    payload = [alert.model_dump(mode="json") for alert in alerts]
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        typer.echo(f"Wrote {len(alerts)} price alert(s) to {output}")
        return
    typer.echo(json.dumps(payload, indent=2))


@app.command("monitoring-brief")
def monitoring_brief(
    input_path: Path = typer.Option(Path("runs/latest/research_run.json"), "--input", help="Research run JSON input."),
    output: Path = typer.Option(Path("runs/latest/monitoring_brief.md"), help="Markdown monitoring brief output path."),
    history: Path | None = typer.Option(None, help="Optional prior trip history YAML path."),
    prices: Path | None = typer.Option(None, help="Optional price history YAML path."),
    destination_limit: int = typer.Option(5, help="Destination ideas to include."),
    drop_threshold_percent: float = typer.Option(10.0, help="Price drop alert threshold."),
) -> None:
    research_run = load_research_run(input_path)
    trip_history = load_trip_history(history) if history else None
    price_history = load_price_history(prices) if prices else None
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        render_monitoring_brief(
            research_run=research_run,
            trip_history=trip_history,
            price_history=price_history,
            destination_limit=destination_limit,
            drop_threshold_percent=drop_threshold_percent,
        ),
        encoding="utf-8",
    )
    typer.echo(f"Wrote monitoring brief to {output}")


@app.command("history-summary")
def history_summary(
    history: Path = typer.Option(Path("data/trip_history.example.yaml"), help="Prior trip history YAML path."),
) -> None:
    trip_history = load_trip_history(history)
    for line in summarize_history(trip_history):
        typer.echo(line)


@app.command("suggest-destinations")
def suggest_destinations_command(
    history: Path = typer.Option(Path("data/trip_history.example.yaml"), help="Prior trip history YAML path."),
    limit: int = typer.Option(8, help="Maximum destination suggestions to print."),
) -> None:
    trip_history = load_trip_history(history)
    suggestions = suggest_destinations(trip_history, limit=limit)
    for index, suggestion in enumerate(suggestions, start=1):
        typer.echo(f"{index}. {suggestion.city}, {suggestion.country} - score {suggestion.score:.3f}")
        for reason in suggestion.reasons:
            typer.echo(f"   - {reason}")


@app.command("draft-watchlist-destinations")
def draft_watchlist_destinations(
    watchlist: Path = typer.Option(Path("data/watchlist.example.yaml"), help="Source watchlist YAML path."),
    history: Path = typer.Option(Path("data/trip_history.example.yaml"), help="Prior trip history YAML path."),
    output: Path = typer.Option(Path("local/watchlist.suggested.yaml"), help="Output watchlist YAML path."),
    earliest_start: datetime = typer.Option(..., formats=["%Y-%m-%d"], help="Earliest date for drafted trips."),
    latest_end: datetime = typer.Option(..., formats=["%Y-%m-%d"], help="Latest date for drafted trips."),
    limit: int = typer.Option(5, help="Maximum new watched trips to add."),
    budget_limit: float | None = typer.Option(None, help="Optional budget limit for drafted trips."),
    nights_min: int = typer.Option(3, help="Minimum nights for drafted trips."),
    nights_max: int = typer.Option(5, help="Maximum nights for drafted trips."),
) -> None:
    watchlist_model = load_watchlist(watchlist)
    trip_history = load_trip_history(history)
    existing_destinations = {trip.destination for trip in watchlist_model.watched_trips}
    drafted = draft_watched_trips(
        history=trip_history,
        existing_destinations=existing_destinations,
        earliest_start=earliest_start.date(),
        latest_end=latest_end.date(),
        limit=limit,
        budget_limit=budget_limit or watchlist_model.profile.max_trip_budget,
        nights_min=nights_min,
        nights_max=nights_max,
    )
    updated = watchlist_model.model_copy(update={"watched_trips": [*watchlist_model.watched_trips, *drafted]})
    write_yaml(output, updated.model_dump(mode="json"))
    typer.echo(f"Wrote watchlist with {len(drafted)} suggested destination(s) to {output}")


@app.command("spotify-auth-url")
def spotify_auth_url(
    state_output: Path = typer.Option(Path("data/spotify/pkce_state.json"), help="PKCE state output path."),
) -> None:
    settings = load_settings()
    if not settings.spotify_client_id:
        raise typer.BadParameter("SPOTIFY_CLIENT_ID is required in .env.local or the environment.")
    pkce_state = create_pkce_state()
    state_output.parent.mkdir(parents=True, exist_ok=True)
    state_output.write_text(json.dumps(pkce_state, indent=2) + "\n", encoding="utf-8")
    url = build_authorization_url(
        client_id=settings.spotify_client_id,
        redirect_uri=settings.spotify_redirect_uri,
        pkce_state=pkce_state,
    )
    typer.echo("Open this Spotify authorization URL, then copy the returned code into spotify-exchange-code:")
    typer.echo(url)


@app.command("spotify-exchange-code")
def spotify_exchange_code(
    code: str = typer.Argument(..., help="Authorization code returned to the redirect URL."),
    state: Path = typer.Option(Path("data/spotify/pkce_state.json"), help="PKCE state JSON path."),
    output: Path = typer.Option(Path("data/spotify/token.json"), help="Spotify token JSON output path."),
) -> None:
    settings = load_settings()
    if not settings.spotify_client_id:
        raise typer.BadParameter("SPOTIFY_CLIENT_ID is required in .env.local or the environment.")
    pkce_state = json.loads(state.read_text(encoding="utf-8"))
    token = exchange_code_for_token(
        client_id=settings.spotify_client_id,
        redirect_uri=settings.spotify_redirect_uri,
        code=code,
        code_verifier=pkce_state["code_verifier"],
    )
    write_token(output, token)
    typer.echo(f"Wrote Spotify token metadata to {output}")


@app.command("spotify-refresh-token")
def spotify_refresh_token(
    token_path: Path = typer.Option(Path("data/spotify/token.json"), help="Spotify token JSON path."),
) -> None:
    settings = load_settings()
    if not settings.spotify_client_id:
        raise typer.BadParameter("SPOTIFY_CLIENT_ID is required in .env.local or the environment.")
    token = load_token(token_path)
    refreshed = refresh_access_token(settings.spotify_client_id, token["refresh_token"])
    write_token(token_path, refreshed)
    typer.echo(f"Refreshed Spotify token metadata in {token_path}")


@app.command("spotify-import-taste")
def spotify_import_taste(
    token_path: Path = typer.Option(Path("data/spotify/token.json"), help="Spotify token JSON path."),
    output: Path = typer.Option(Path("data/music_taste/latest.yaml"), help="Music taste YAML output path."),
    top_limit: int = typer.Option(50, help="Top artists to import, max 50."),
    followed_limit: int = typer.Option(50, help="Followed artists to import."),
) -> None:
    settings = load_settings()
    access_token = get_valid_spotify_access_token(settings.spotify_client_id, token_path)
    taste = import_music_taste(
        access_token=access_token,
        top_limit=top_limit,
        followed_limit=followed_limit,
    )
    write_yaml(output, taste.model_dump(mode="json"))
    typer.echo(f"Wrote {len(taste.artists)} Spotify artist(s) to {output}")


@app.command("calendar-auth-url")
def calendar_auth_url(
    state_output: Path = typer.Option(Path("data/google/pkce_state.json"), help="Google PKCE state output path."),
) -> None:
    settings = load_settings()
    if not settings.google_client_id:
        raise typer.BadParameter("GOOGLE_CLIENT_ID is required in .env.local or the environment.")
    pkce_state = create_google_pkce_state()
    state_output.parent.mkdir(parents=True, exist_ok=True)
    state_output.write_text(json.dumps(pkce_state, indent=2) + "\n", encoding="utf-8")
    url = build_google_authorization_url(
        client_id=settings.google_client_id,
        redirect_uri=settings.google_redirect_uri,
        pkce_state=pkce_state,
    )
    typer.echo("Open this Google authorization URL, then copy the returned code into calendar-exchange-code:")
    typer.echo(url)


@app.command("calendar-exchange-code")
def calendar_exchange_code(
    code: str = typer.Argument(..., help="Authorization code returned to the redirect URL."),
    state: Path = typer.Option(Path("data/google/pkce_state.json"), help="Google PKCE state JSON path."),
    output: Path = typer.Option(Path("data/google/token.json"), help="Google token JSON output path."),
) -> None:
    settings = load_settings()
    if not settings.google_client_id:
        raise typer.BadParameter("GOOGLE_CLIENT_ID is required in .env.local or the environment.")
    pkce_state = json.loads(state.read_text(encoding="utf-8"))
    token = exchange_google_code_for_token(
        client_id=settings.google_client_id,
        redirect_uri=settings.google_redirect_uri,
        code=code,
        code_verifier=pkce_state["code_verifier"],
    )
    write_google_token(output, token)
    typer.echo(f"Wrote Google token metadata to {output}")


@app.command("calendar-refresh-token")
def calendar_refresh_token(
    token_path: Path = typer.Option(Path("data/google/token.json"), help="Google token JSON path."),
) -> None:
    settings = load_settings()
    if not settings.google_client_id:
        raise typer.BadParameter("GOOGLE_CLIENT_ID is required in .env.local or the environment.")
    token = load_google_token(token_path)
    refreshed = refresh_google_access_token(settings.google_client_id, token["refresh_token"])
    write_google_token(token_path, refreshed)
    typer.echo(f"Refreshed Google token metadata in {token_path}")


@app.command("calendar-import-busy")
def calendar_import_busy(
    token_path: Path = typer.Option(Path("data/google/token.json"), help="Google token JSON path."),
    output: Path = typer.Option(Path("local/calendar_snapshot.yaml"), help="Calendar snapshot YAML output path."),
    range_start: datetime = typer.Option(..., formats=["%Y-%m-%dT%H:%M:%S%z"], help="Range start timestamp."),
    range_end: datetime = typer.Option(..., formats=["%Y-%m-%dT%H:%M:%S%z"], help="Range end timestamp."),
    timezone: str = typer.Option("Europe/London", help="Calendar timezone."),
) -> None:
    settings = load_settings()
    access_token = get_valid_google_access_token(settings.google_client_id, token_path)
    snapshot = import_freebusy_snapshot(
        access_token=access_token,
        calendar_id=settings.google_calendar_id,
        timezone=timezone,
        range_start=range_start,
        range_end=range_end,
    )
    write_yaml(output, snapshot.model_dump(mode="json"))
    typer.echo(f"Wrote {len(snapshot.busy_events)} busy event(s) to {output}")


@app.command("ticketmaster-search")
def ticketmaster_search(
    city: str = typer.Argument(..., help="City to search."),
    starts_on: datetime = typer.Option(..., formats=["%Y-%m-%d"], help="Start date."),
    ends_on: datetime = typer.Option(..., formats=["%Y-%m-%d"], help="End date."),
    output: Path = typer.Option(Path("local/ticketmaster_events.yaml"), help="Event options YAML output path."),
    size: int = typer.Option(20, help="Maximum events to fetch."),
) -> None:
    settings = load_settings()
    if not settings.ticketmaster_api_key:
        raise typer.BadParameter("TICKETMASTER_API_KEY is required in .env.local or the environment.")
    events = search_music_events(
        api_key=settings.ticketmaster_api_key,
        city=city,
        starts_on=starts_on.date(),
        ends_on=ends_on.date(),
        size=size,
    )
    write_yaml(output, {"event_options": [event.model_dump(mode="json") for event in events]})
    typer.echo(f"Wrote {len(events)} Ticketmaster event option(s) to {output}")


@app.command("attach-events")
def attach_events(
    trip_name: str = typer.Argument(..., help="Watched trip name to attach events to."),
    events: Path = typer.Option(..., help="YAML file containing event_options."),
    output: Path = typer.Option(Path("local/manual_findings.events.yaml"), help="Manual findings YAML output path."),
    start_date: datetime | None = typer.Option(None, formats=["%Y-%m-%d"], help="Optional trip start date."),
    end_date: datetime | None = typer.Option(None, formats=["%Y-%m-%d"], help="Optional trip end date."),
    calendar_fit: bool | None = typer.Option(None, help="Optional known calendar fit."),
) -> None:
    event_options = load_event_options(events)
    findings = ManualFindings(
        trips={
            trip_name: ManualTripFindings(
                start_date=start_date.date() if start_date else None,
                end_date=end_date.date() if end_date else None,
                calendar_fit=calendar_fit,
                event_options=event_options,
                notes=[f"Attached {len(event_options)} event option(s) from {events}."],
            )
        }
    )
    write_yaml(output, findings.model_dump(mode="json"))
    typer.echo(f"Wrote manual findings for {trip_name!r} with {len(event_options)} event option(s) to {output}")


@app.command("attach-transport")
def attach_transport(
    trip_name: str = typer.Argument(..., help="Watched trip name to attach transport to."),
    transport: Path = typer.Option(..., help="YAML file containing transport_options."),
    output: Path = typer.Option(Path("local/manual_findings.transport.yaml"), help="Manual findings YAML output path."),
    start_date: datetime | None = typer.Option(None, formats=["%Y-%m-%d"], help="Optional trip start date."),
    end_date: datetime | None = typer.Option(None, formats=["%Y-%m-%d"], help="Optional trip end date."),
    calendar_fit: bool | None = typer.Option(None, help="Optional known calendar fit."),
) -> None:
    transport_options = load_transport_options(transport)
    findings = ManualFindings(
        trips={
            trip_name: ManualTripFindings(
                start_date=start_date.date() if start_date else None,
                end_date=end_date.date() if end_date else None,
                calendar_fit=calendar_fit,
                transport_options=transport_options,
                notes=[f"Attached {len(transport_options)} transport option(s) from {transport}."],
            )
        }
    )
    write_yaml(output, findings.model_dump(mode="json"))
    typer.echo(f"Wrote manual findings for {trip_name!r} with {len(transport_options)} transport option(s) to {output}")


@app.command("attach-accommodation")
def attach_accommodation(
    trip_name: str = typer.Argument(..., help="Watched trip name to attach accommodation to."),
    accommodation: Path = typer.Option(..., help="YAML file containing accommodation_options."),
    output: Path = typer.Option(Path("local/manual_findings.accommodation.yaml"), help="Manual findings YAML output path."),
    start_date: datetime | None = typer.Option(None, formats=["%Y-%m-%d"], help="Optional trip start date."),
    end_date: datetime | None = typer.Option(None, formats=["%Y-%m-%d"], help="Optional trip end date."),
    calendar_fit: bool | None = typer.Option(None, help="Optional known calendar fit."),
) -> None:
    accommodation_options = load_accommodation_options(accommodation)
    findings = ManualFindings(
        trips={
            trip_name: ManualTripFindings(
                start_date=start_date.date() if start_date else None,
                end_date=end_date.date() if end_date else None,
                calendar_fit=calendar_fit,
                accommodation_options=accommodation_options,
                notes=[f"Attached {len(accommodation_options)} accommodation option(s) from {accommodation}."],
            )
        }
    )
    write_yaml(output, findings.model_dump(mode="json"))
    typer.echo(
        f"Wrote manual findings for {trip_name!r} with {len(accommodation_options)} accommodation option(s) to {output}"
    )


@app.command("merge-findings")
def merge_findings(
    inputs: list[Path] = typer.Argument(..., help="Manual findings YAML files to merge."),
    output: Path = typer.Option(Path("local/manual_findings.merged.yaml"), help="Merged manual findings YAML output path."),
) -> None:
    merged = ManualFindings()
    for input_path in inputs:
        findings = load_manual_findings(input_path)
        merged.calendar_windows.extend(findings.calendar_windows)
        for trip_name, trip_findings in findings.trips.items():
            existing = merged.trips.get(trip_name)
            if existing is None:
                merged.trips[trip_name] = trip_findings
                continue
            existing.start_date = existing.start_date or trip_findings.start_date
            existing.end_date = existing.end_date or trip_findings.end_date
            existing.calendar_fit = existing.calendar_fit if existing.calendar_fit is not None else trip_findings.calendar_fit
            existing.transport_options.extend(trip_findings.transport_options)
            existing.event_options.extend(trip_findings.event_options)
            existing.accommodation_options.extend(trip_findings.accommodation_options)
            existing.cost_components.extend(trip_findings.cost_components)
            existing.notes.extend(trip_findings.notes)
    write_yaml(output, merged.model_dump(mode="json"))
    typer.echo(f"Merged {len(inputs)} manual findings file(s) into {output}")


@app.command("research-brief")
def research_brief(
    trip_name: str = typer.Argument(..., help="Watched trip name to brief."),
    watchlist: Path = typer.Option(Path("data/watchlist.example.yaml"), help="Watchlist YAML path."),
    output: Path = typer.Option(Path("local/research_brief.md"), help="Markdown brief output path."),
) -> None:
    watchlist_model = load_watchlist(watchlist)
    trip = _find_watched_trip(watchlist_model, trip_name)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_research_brief(watchlist_model, trip), encoding="utf-8")
    typer.echo(f"Wrote research brief for {trip.name!r} to {output}")


@app.command("create-option-templates")
def create_option_templates(
    trip_name: str = typer.Argument(..., help="Watched trip name to template."),
    watchlist: Path = typer.Option(Path("data/watchlist.example.yaml"), help="Watchlist YAML path."),
    output_dir: Path = typer.Option(Path("local"), help="Output directory."),
) -> None:
    watchlist_model = load_watchlist(watchlist)
    trip = _find_watched_trip(watchlist_model, trip_name)
    slug = "".join(character.lower() if character.isalnum() else "-" for character in trip.name).strip("-")
    write_yaml(output_dir / f"{slug}.transport.yaml", transport_template(watchlist_model, trip))
    write_yaml(output_dir / f"{slug}.accommodation.yaml", accommodation_template(watchlist_model, trip))
    write_yaml(output_dir / f"{slug}.events.yaml", events_template(watchlist_model, trip))
    typer.echo(f"Wrote option templates for {trip.name!r} to {output_dir}")


@app.command("trip-pack")
def trip_pack(
    trip_name: str = typer.Argument(..., help="Watched trip name to prepare."),
    watchlist: Path = typer.Option(Path("data/watchlist.example.yaml"), help="Watchlist YAML path."),
    output_dir: Path = typer.Option(Path("local/trip_pack"), help="Output directory."),
) -> None:
    watchlist_model = load_watchlist(watchlist)
    trip = _find_watched_trip(watchlist_model, trip_name)
    slug = "".join(character.lower() if character.isalnum() else "-" for character in trip.name).strip("-")
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / f"{slug}.brief.md").write_text(render_research_brief(watchlist_model, trip), encoding="utf-8")
    write_yaml(output_dir / f"{slug}.transport.yaml", transport_template(watchlist_model, trip))
    write_yaml(output_dir / f"{slug}.accommodation.yaml", accommodation_template(watchlist_model, trip))
    write_yaml(output_dir / f"{slug}.events.yaml", events_template(watchlist_model, trip))
    typer.echo(f"Wrote trip research pack for {trip.name!r} to {output_dir}")


def _find_watched_trip(watchlist, trip_name: str):
    for trip in watchlist.watched_trips:
        if trip.name.lower() == trip_name.lower():
            return trip
    raise typer.BadParameter(f"No watched trip named {trip_name!r} found in watchlist.")


if __name__ == "__main__":
    app()
