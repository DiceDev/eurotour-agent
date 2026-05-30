# EuroTour Agent Report

- Generated: 2026-05-30T18:07:06.042244+00:00
- Mode: dry-run-fixture-plus-manual
- Watchlist: `data\watchlist.example.yaml`

## Calendar Windows

- 2026-07-01T00:00:00+01:00 to 2026-07-04T23:59:00+01:00 (Example open long weekend)

## Recommendations

### 1. Book Berlin

- Trip: Berlin long weekend
- Decision: book
- Score: 0.850
- Estimated tracked cost: 233.00 USD

Berlin from 2026-07-01 to 2026-07-04: 1 transport option(s), 1 event option(s), score 0.850.

Reasons:
- Composite score is 0.850.
- Best event signal is Example Electronic Act in Berlin with relevance 0.82.
- Lowest tracked flight option is 185.00 USD.
- Estimated tracked cost is 233.00 against budget 900.00.

Risks:
- Manual findings need primary-source re-check before money changes hands.

Next actions:
- Verify calendar availability.
- Confirm fare and ticket availability on primary sources.
- Prepare booking checklist; do not purchase automatically.

### 2. Watch Amsterdam

- Trip: Amsterdam by rail
- Decision: watch
- Score: 0.723
- Estimated tracked cost: 242.78 USD

Amsterdam from 2026-07-01 to 2026-07-03: 1 transport option(s), 1 event option(s), score 0.723.

Reasons:
- Composite score is 0.723.
- Best event signal is Priority artist TBD in Amsterdam with relevance 0.55.
- Lowest tracked train option is 177.78 USD.
- Estimated tracked cost is 242.78 against budget 800.00.

Risks:
- Transport prices are fixture estimates, not live fares.
- Concert data is fixture output, not live inventory.

Next actions:
- Refresh transport prices from primary or aggregator sources.
- Refresh concert discovery from Spotify, Bandsintown, Songkick, DICE, RA, and venue calendars.
- Re-rank after calendar fit is confirmed.

## Source Notes

- Dry-run data is deterministic fixture output for workflow validation.
- Manual findings are treated as user/chat-researched provisional data.
- Verify fares and tickets against primary airline, operator, venue, or ticketing pages before acting.
