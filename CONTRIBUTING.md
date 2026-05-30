# Contributing

EuroTour Agent is a local-first Python project. Keep changes small, tested, and boring in the best possible way.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

## Validation

Run this before committing:

```powershell
python -m pytest -q
python -m compileall src tests
python -m eurotour_agent.scheduler doctor
```

## Data And Secrets

Do not commit real OAuth tokens, API keys, calendar exports, or personal trip records. Use `local/` for private working files and keep committed data under `data/` limited to examples or sanitized fixtures.

Ignored private files include:

- `.env.local`
- `data/spotify/token*.json`
- `data/spotify/pkce_state*.json`
- `data/google/token*.json`
- `data/google/pkce_state*.json`
- `local/`
- `runs/`

## Recommendation Rules

The planner should never claim something is bookable without primary-source verification. Any live provider integration should preserve the existing `research_needed` and `ready_to_verify` distinction, because accidentally buying a flight through vibes would be very 2026 in the worst way.
