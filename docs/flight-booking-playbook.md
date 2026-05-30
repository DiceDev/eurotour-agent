# Flight Price and Booking Playbook

Research checked on 2026-05-30.

## Default Search Stack

Use multiple tools because each one is wrong in a different way:

1. Google Flights for fast route discovery, flexible dates, price graph, date grid, price tracking, and fare-history hints.
2. Skyscanner for broad "everywhere" discovery and flexible destination exploration.
3. KAYAK for extra alerts, flexible windows, and nearby-airport checks.
4. ITA Matrix when the route is complex and fare/routing control matters.
5. Airline websites for final price, fare rules, baggage rules, and booking.

Sources:

- Google Flights fare tools: https://support.google.com/travel/answer/7664728
- Google Flights tracking: https://support.google.com/travel/answer/6235879
- KAYAK price alerts and fee notes: https://www.kayak.com/c/help/pricing/
- ITA Matrix: https://matrix.itasoftware.com/search
- Skyscanner flexible/everywhere search: https://www.skyscanner.com/tips-and-inspiration/deals/new-daily-cheapest-flights-deals

## Booking Rules

- Prefer booking directly with the airline unless the third-party saving is large enough to justify worse support.
- Confirm final fare on the airline site before calling anything a deal.
- Compare total trip cost, not headline fare: baggage, seat selection, airport transfer, arrival time, and refund/change rules.
- Avoid self-transfer itineraries unless the layover is generous and the savings are meaningful.
- Prefer one ticket for protected connections. Separate tickets can be cheaper, but missed-connection protection usually disappears.
- For short Europe trips, punish bad flight times heavily. A cheap 06:00 departure can destroy the first day.
- Check alternate airports only when transfer cost and time are explicitly included.

## Price Tracking Rules

Track searches at three levels:

- Route/date window: broad watch for "London to Berlin, any Fri-Mon in September."
- Exact itinerary: watch a specific flight pair once it becomes likely.
- Backup route: watch a nearby airport or train alternative.

Use alert thresholds:

- Meaningful drop: 10-15%.
- Book-now candidate: below historic/typical range, calendar-compatible, and total cost fits budget.
- Escalate immediately: rare route, festival/concert weekend, school holiday, or only a few reasonable nonstop flights.

## Timing Heuristics

These are heuristics, not laws. Airlines are yield-management machines, not your pals.

- For Europe short-haul, start watching 2-5 months out.
- For peak summer, major holidays, festivals, and scarce routes, start earlier.
- For long-haul Europe trips, start watching 4-8 months out.
- Do not wait for a mythical Tuesday deal if the price is already good and the itinerary is sane.
- If a good fare appears for a fixed event trip, book once the budget and calendar check pass.

## Refund and Passenger Rights Notes

United States:

- DOT rules require covered airlines to offer either a 24-hour hold or a 24-hour cancellation refund for qualifying reservations made at least 7 days before departure.
- The DOT notes this 24-hour rule does not apply to tickets booked through online travel agencies or other third-party agents.
- Source: https://www.transportation.gov/individuals/aviation-consumer-protection/refunds

European Union:

- EU air passenger rights may apply for denied boarding, cancellation, and long delays, including reimbursement/rerouting/assistance in qualifying cases.
- Source: https://europa.eu/youreurope/citizens/travel/passenger-rights/air/index_en.htm

## Europe-Specific Airport Notes

- London: compare LHR, LGW, STN, LTN, LCY, but include transfer penalties. STN/LTN can be false economy for bad timings.
- Paris: CDG and ORY are both usable; Beauvais can be punishing unless the fare is absurdly cheap.
- Milan: LIN is convenient, MXP common, BGY often cheap but farther.
- Brussels: BRU is normal; Charleroi can add friction.
- Stockholm/Oslo/Barcelona/Rome: cheap airports can still be good, but only after transfer math.

## What The Agent Should Record

For every candidate flight:

- Search timestamp.
- Source.
- Booking provider.
- Fare price and currency.
- Baggage assumptions.
- Departure/arrival airports.
- Door-to-door estimate.
- Layover risk.
- Refund/change notes.
- Why it is or is not worth watching.

## Decision Framework

Score flights by:

- Calendar fit.
- Total cost.
- Door-to-door time.
- Schedule quality.
- Connection risk.
- Booking reliability.
- Baggage/fare restrictions.
- Passenger-rights posture.

The cheapest fare only wins if it survives the rest of the list. Yes, this is where many travel sites quietly insult your intelligence.
