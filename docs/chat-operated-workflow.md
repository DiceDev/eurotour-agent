# Chat-Operated Workflow

For v1, Codex/chat is the recommendation engine. The project stores preferences, watchlists, provider notes, and repeatable commands.

## Operating Model

1. Keep trip ideas and watched routes in `data/watchlist.example.yaml` or a copied local file.
2. Ask Codex to refresh a specific trip idea, date window, route, artist, or city.
3. Codex researches current options, updates notes, and summarizes tradeoffs.
4. Only promote something to API automation after the manual loop proves it is worth checking repeatedly.

## Good Prompts

```text
Check my calendar for open 3-5 day windows in July and compare them against the current watchlist.
```

```text
Refresh Lisbon, Berlin, and Barcelona for concerts by artists similar to my Spotify favorites, then rank the trips under $900.
```

```text
Track flights and trains from London to Amsterdam for the first two September weekends. Update the watchlist with best current options.
```

```text
Build a realistic itinerary for the strongest option, including buffers and a budget.
```

## Scheduling Reality

Codex can help create local scheduled jobs, but this chat does not keep running after the session ends unless a real scheduler is configured.

Practical options:

- Manual: ask Codex to run a refresh when you care.
- Local: Windows Task Scheduler runs `eurotour-agent` on a cadence.
- Hosted: GitHub Actions, Vercel Cron, or another worker runs checks and sends summaries.

## Promotion Rule

Do not automate a source just because it exists. Automate it when manual use shows it repeatedly changes the recommendation.

