# EuroTour Agent

Personal automated travel agent for Europe-focused trips, live music discovery, calendar-aware itinerary planning, and travel price monitoring.

Default home base: Cheltenham, UK. Preferred airports start with Bristol (`BRS`) and Birmingham (`BHX`).

## What This Is

This project is scaffolded as API-ready but API-optional. The first version can collect preferences, model trips, track candidate searches, and run provider checks without requiring an OpenAI API key. A later API-backed recommendation engine can be added behind the same planner interface.

## Core Jobs

- Read existing schedule constraints from Google Calendar.
- Track candidate trips, destinations, concerts, flights, trains, and lodging.
- Run recurring checks for price and availability changes.
- Maintain trip budgets and itinerary versions.
- Generate recommendations from current options and saved preferences.
- Keep cost controls explicit before any AI or paid travel-data API is used.

## Project Layout

```text
.
+-- docs/
|   +-- cost-estimates.md
|   +-- product-plan.md
|   +-- flight-booking-playbook.md
|   +-- concert-discovery-playbook.md
|   +-- chat-operated-workflow.md
|   +-- provider-notes.md
|   +-- routine-automation.md
+-- data/
|   +-- watchlist.example.yaml
|   +-- trip_history.example.yaml
|   +-- price_history.example.yaml
+-- src/
|   +-- eurotour_agent/
|       +-- __init__.py
|       +-- config.py
|       +-- models.py
|       +-- planner.py
|       +-- scheduler.py
|       +-- providers/
|           +-- __init__.py
|           +-- calendar.py
|           +-- concerts.py
|           +-- music.py
|           +-- transport.py
+-- .env.example
+-- .gitignore
+-- pyproject.toml
+-- scripts/
|   +-- daily_brief.ps1
```

## Quick Start

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
python -m eurotour_agent.scheduler --dry-run
python -m eurotour_agent.scheduler refresh-watchlist
python -m eurotour_agent.scheduler refresh-watchlist --findings data\manual_findings.example.yaml
python -m eurotour_agent.scheduler find-free-windows --calendar data\calendar_snapshot.example.yaml
python -m eurotour_agent.scheduler refresh-watchlist --findings data\manual_findings.sample-2026-05-30.yaml --music-taste data\music_taste\sample.yaml --rates data\currency_rates.example.yaml
python -m eurotour_agent.scheduler refresh-watchlist --history data\trip_history.example.yaml
python -m eurotour_agent.scheduler daily-brief-run --findings data\manual_findings.sample-2026-05-30.yaml --music-taste data\music_taste\sample.yaml --rates data\currency_rates.example.yaml --history data\trip_history.example.yaml --prices data\price_history.example.yaml
python -m eurotour_agent.scheduler rank
python -m eurotour_agent.scheduler report
python -m eurotour_agent.scheduler audit-run
python -m eurotour_agent.scheduler price-alerts --history data\price_history.example.yaml
python -m eurotour_agent.scheduler monitoring-brief --input runs\latest\research_run.json --prices data\price_history.example.yaml --history data\trip_history.example.yaml
python -m eurotour_agent.scheduler doctor
python -m eurotour_agent.scheduler history-summary --history data\trip_history.example.yaml
python -m eurotour_agent.scheduler suggest-destinations --history data\trip_history.example.yaml --limit 5
python -m eurotour_agent.scheduler draft-watchlist-destinations --history data\trip_history.example.yaml --earliest-start 2026-10-01 --latest-end 2026-12-31 --limit 3
python -m eurotour_agent.scheduler attach-events "Berlin long weekend" --events local\ticketmaster_events.yaml
python -m eurotour_agent.scheduler attach-transport "Berlin long weekend" --transport local\transport_options.yaml
python -m eurotour_agent.scheduler attach-accommodation "Berlin long weekend" --accommodation local\accommodation_options.yaml
python -m eurotour_agent.scheduler merge-findings local\manual_findings.events.yaml local\manual_findings.transport.yaml local\manual_findings.accommodation.yaml
python -m eurotour_agent.scheduler research-brief "Berlin long weekend" --output local\berlin-brief.md
python -m eurotour_agent.scheduler create-option-templates "Berlin long weekend" --output-dir local
python -m eurotour_agent.scheduler trip-pack "Berlin long weekend" --output-dir local\berlin-pack
python -m eurotour_agent.scheduler validate-file local\berlin-long-weekend.transport.yaml --kind transport
```

If your Python scripts directory is on `PATH`, the installed `eurotour-agent` command can be used instead of `python -m eurotour_agent.scheduler`.

## Configuration

Copy `.env.example` to `.env.local` when you are ready to connect providers.

No secrets are required for the dry-run scaffold.

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for local setup, validation commands, and the rules for keeping real tokens and personal data out of git.

See [docs/routine-automation.md](docs/routine-automation.md) for the daily brief command and Windows Task Scheduler setup.

## Current Cost Posture

Start with the local scheduler and free-tier/provider-approved APIs where possible. Add OpenAI API recommendations only after the search and itinerary data model is stable. See [docs/cost-estimates.md](docs/cost-estimates.md).

## V1 Operating Mode

For now, this chat can act as the recommendation engine while the project stores the durable structure. See [docs/chat-operated-workflow.md](docs/chat-operated-workflow.md), then copy [data/watchlist.example.yaml](data/watchlist.example.yaml) when you are ready to track real trip ideas.

## Local Outputs

- `runs/latest/research_run.json`: normalized candidate trips from the latest refresh.
- `runs/latest/summary.json`: compact machine-readable run manifest for notification layers.
- `runs/latest/report.md`: readable recommendation report.
- `runs/latest/monitoring_brief.md`: concise recommendation, price-alert, and destination-idea brief.

Dry-run refreshes use deterministic fixture data. Treat every fare and ticket as provisional until checked against a primary source.

Use `data/manual_findings.example.yaml` as the shape for chat-researched fares, concert options, and calendar windows. Manual findings are merged into the watchlist during refreshes.

Trip reports include transport, accommodation, event tickets, local transit, food/drink, and buffer estimates when those values are available.

`data/trip_history.example.yaml` records prior trips, ratings, tags, likes, dislikes, and repeat signals. Add it to `refresh-watchlist` with `--history` so recommendations can learn from good past patterns while penalizing destinations that have become too repetitive. Computers, regrettably, will otherwise keep rediscovering Berlin forever.

Use `suggest-destinations` to turn prior trip tags into new Europe destination ideas before adding them to the watchlist.

Use `draft-watchlist-destinations` to write those suggestions into a new watchlist file under `local/`, ready for `refresh-watchlist`.

`data/price_history.example.yaml` stores repeated fare, lodging, and ticket observations. Use `price-alerts` to flag latest drops and new tracked lows.

Use `daily-brief-run` for the routine agent pass. It writes the normalized research run, ranked recommendations, price alerts, detailed report, and monitoring brief in one output directory.

`data/calendar_snapshot.example.yaml` shows the shape future Google Calendar reads should feed into the app: busy events in, free travel windows out.

Spotify integration is optional. Use `spotify-auth-url`, `spotify-exchange-code`, and `spotify-import-taste` after setting `SPOTIFY_CLIENT_ID` and an allowed redirect URI in `.env.local`. Token files under `data/spotify/` are ignored by git.
