# Routine Automation

The local automation target is `daily-brief-run`. It produces the files an automated travel check needs:

- `research_run.json`
- `summary.json`
- `notification_digest.md`
- `recommendations.json`
- `price_alerts.json`
- `report.md`
- `monitoring_brief.md`

## Manual Run

```powershell
python -m eurotour_agent.scheduler daily-brief-run `
  --findings data\manual_findings.sample-2026-05-30.yaml `
  --music-taste data\music_taste\sample.yaml `
  --rates data\currency_rates.example.yaml `
  --history data\trip_history.example.yaml `
  --prices data\price_history.example.yaml `
  --output-dir runs\latest
```

## PowerShell Wrapper

```powershell
.\scripts\daily_brief.ps1 `
  -Findings data\manual_findings.sample-2026-05-30.yaml `
  -MusicTaste data\music_taste\sample.yaml `
  -Rates data\currency_rates.example.yaml
```

The wrapper defaults to the sample trip history and price history. Use `local\` paths for private real data.

## Windows Task Scheduler

Create a scheduled task from PowerShell:

```powershell
$project = "C:\Users\claya\Documents\GitHub\eurotour-agent"
$action = New-ScheduledTaskAction `
  -Execute "powershell.exe" `
  -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$project\scripts\daily_brief.ps1`" -ProjectRoot `"$project`" -OutputDir `"runs\latest`""
$trigger = New-ScheduledTaskTrigger -Daily -At 08:00
Register-ScheduledTask `
  -TaskName "EuroTour Agent Daily Brief" `
  -Action $action `
  -Trigger $trigger `
  -Description "Generate EuroTour travel, music, and price monitoring brief."
```

This creates files locally only. It does not book anything, send messages, or spend API money. Good. Let the software earn trust before it gets a credit card.

## Notification Digest

The daily run writes `notification_digest.md`, a compact message suitable for email, chat, or manual review. Rebuild it from an existing run with:

```powershell
python -m eurotour_agent.scheduler render-notification `
  --summary runs\latest\summary.json `
  --monitoring-brief runs\latest\monitoring_brief.md `
  --output runs\latest\notification_digest.md
```

## Private Data

Keep real exports and provider outputs under `local\`, for example:

```powershell
.\scripts\daily_brief.ps1 `
  -Watchlist local\watchlist.yaml `
  -Findings local\manual_findings.yaml `
  -MusicTaste local\music_taste.yaml `
  -History local\trip_history.yaml `
  -Prices local\price_history.yaml `
  -OutputDir runs\latest
```
