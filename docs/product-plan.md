# Product Plan

## V1 Scope

The first version should answer:

- Where can I go in Europe during my real open calendar windows?
- Which destinations have relevant live music during those windows?
- What are the plausible transport options and rough budgets?
- Which trips are worth watching for better prices?
- What changed since the last scan?

## Core Entities

- Preference profile: home base, airports/stations, budget style, pace, favorite genres/artists, disliked constraints.
- Calendar window: free blocks, busy blocks, hard constraints, soft constraints.
- Candidate trip: destination, dates, reason, budget, confidence, status.
- Transport option: flight/train/bus route, provider, price, timing, baggage/change notes, fetch timestamp.
- Event option: artist, venue, city, date, ticket link, price if known, relevance score.
- Itinerary item: travel, lodging, concert, food, buffer, recovery time.

## Automation Loop

1. Read upcoming calendar windows.
2. Refresh saved route and event searches.
3. Normalize transport and concert options.
4. Compare against budget and preference rules.
5. Produce a short change report.
6. Escalate only meaningful recommendations.

## Calendar Fit

Google Calendar integration should normalize busy events into a `CalendarSnapshot`, then compute free travel windows with configurable minimum nights and buffers around busy events. The planner should treat these windows as evidence, not guesswork.

## Recommendation Strategy

Use deterministic rules first:

- Calendar fit.
- Total expected cost.
- Travel time.
- Overnight count.
- Event relevance.
- Price drop since last check.

Use AI second:

- Explain tradeoffs.
- Rank fuzzy options.
- Build itinerary drafts.
- Suggest alternatives from music taste and travel preferences.

## Later Features

- Google Calendar event draft creation.
- Spotify liked artists and playlists import.
- Price-watch alerts.
- Trip dossiers with packing, visas, transit, neighborhood notes.
- Budget ledger and post-trip actuals.
