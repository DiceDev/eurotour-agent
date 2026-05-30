# EuroTour Agent Report

- Generated: 2026-05-30T18:26:03.589258+00:00
- Mode: dry-run-fixture-plus-manual
- Watchlist: `data\watchlist.example.yaml`

## Calendar Windows

- 2026-07-03T00:00:00+01:00 to 2026-07-06T23:59:00+01:00 (Sample Berlin electronic weekend)
- 2026-07-02T00:00:00+01:00 to 2026-07-05T23:59:00+01:00 (Sample Amsterdam indie weekend)

## Recommendations

### 1. Book Berlin

- Trip: Berlin long weekend
- Decision: book
- Score: 0.842
- Estimated tracked cost: 855.00 USD (partial)
- Missing cost categories: transport, event

Berlin from 2026-07-03 to 2026-07-06: 2 transport option(s), 2 event option(s), score 0.842.

Reasons:
- Composite score is 0.842.
- Best event signal is Sanctum of Sound Festival in Berlin with relevance 0.86.
- Estimated tracked cost is 855.00 USD against budget 900.00.

Cost breakdown:
- accommodation: Berlin mid-range hotel estimate - 450.00 USD
- local_transit: Berlin airport transfers and BVG transit - 45.00 USD
- food_drink: Food and drink, 4 days - 260.00 USD
- buffer: Trip buffer - 100.00 USD

Risks:
- Manual findings need primary-source re-check before money changes hands.
- Total trip estimate is incomplete; missing priced categories: transport, event.
- Baggage and fare restrictions need primary-source verification.

Next actions:
- Verify calendar availability.
- Confirm fare and ticket availability on primary sources.
- Prepare booking checklist; do not purchase automatically.

### 2. Book Amsterdam

- Trip: Amsterdam by rail
- Decision: book
- Score: 0.779
- Missing cost categories: event

Amsterdam from 2026-07-02 to 2026-07-05: 3 transport option(s), 2 event option(s), score 0.779.

Reasons:
- Composite score is 0.779.
- Best event signal is Kevin Morby and Liam Kazar in Amsterdam with relevance 0.93.
- Lowest tracked train option is 130.00 EUR.

Cost breakdown:
- transport: train: Cheltenham Spa to Amsterdam Centraal - 130.00 EUR
- accommodation: Amsterdam mid-range hotel estimate - 570.00 USD
- local_transit: Amsterdam airport/station transfers and GVB transit - 55.00 USD
- food_drink: Food and drink, 4 days - 280.00 USD
- buffer: Trip buffer - 110.00 USD

Risks:
- Manual findings need primary-source re-check before money changes hands.
- Tracked costs are not in the budget currency; convert before treating the budget score as reliable.
- Total trip estimate is incomplete; missing priced categories: event.
- Baggage and fare restrictions need primary-source verification.

Next actions:
- Verify calendar availability.
- Confirm fare and ticket availability on primary sources.
- Prepare booking checklist; do not purchase automatically.

## Source Notes

- Dry-run data is deterministic fixture output for workflow validation.
- Manual findings are treated as user/chat-researched provisional data.
- Verify fares and tickets against primary airline, operator, venue, or ticketing pages before acting.
