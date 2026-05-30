# Provider Decision Matrix

Research date: 2026-05-30

Goal: choose low-risk providers for a personal Europe travel and music agent based in Cheltenham, UK. The app should collect options, price signals, and verification tasks. It should not book or purchase automatically.

## Summary

| Domain | Provider | Decision | Why |
| --- | --- | --- | --- |
| Calendar | Google Calendar | Keep implemented | Read-only free/busy is enough to identify trip windows. |
| Music taste | Spotify Web API | Keep implemented | Top/followed artists map cleanly to event searches. |
| Events | Ticketmaster Discovery API | Keep implemented, first live source | Good structured city/date event search, but misses some smaller venues. |
| Flights | Amadeus Flight Offers | Next integration | Search plus price-confirmation flow fits flight monitoring. |
| Hotels | Amadeus Hotel Search | Next integration after flights | Structured availability and price checks; booking remains off. |
| UK rail/live ground transport | National Rail Darwin | Research only | Official real-time train running data, not fare shopping. |
| UK rail/bus/multimodal | TransportAPI | Candidate | Good UK transport data candidate if pricing and terms fit personal use. |
| Rail retail | Trainline partner/affiliate | Manual for now | Partner/API access appears commercial/approval-based. |
| Secondary music | Bandsintown, Songkick, DICE, venues | Manual/secondary | Useful for smaller acts; API availability/terms vary and need verification. |

## Provider Notes

### Amadeus Flights

Official docs say the Flights category covers searching through booking, including Flight Offers Search, Flight Offers Price, Flight Create Orders, order management, seatmaps, branded fares, inspiration, cheapest dates, availability, and flight status.

Implementation stance:

- Use Flight Inspiration/Cheapest Date only for scouting; docs state these use cached/dynamic cache data.
- Use Flight Offers Search for dated options.
- Use Flight Offers Price before any `ready_to_verify` decision.
- Do not use Create Orders or ticket issuance unless the user explicitly promotes the app to a booking tool. That is later-problem territory with paperwork attached.

Source: https://developers.amadeus.com/self-service/apis-docs/guides/developer-guides/resources/flights/

### Amadeus Hotels

Official docs list Hotel List, Hotel Ratings, Hotel Search, Hotel Booking, and autocomplete. Hotel List can search by city code, geocode, or hotel IDs; Hotel Search provides cheapest hotels in a location with filters; Hotel Booking is a separate step.

Implementation stance:

- Start with hotel list/search for availability and estimated lodging cost.
- Keep bookings out of scope.
- Treat cancellation/refundability as primary-source verification until normalized reliably.

Source: https://developers.amadeus.com/self-service/apis-docs/guides/developer-guides/resources/hotels/

### Ticketmaster Discovery API

Ticketmaster Discovery is the first structured live event source already represented in code. It is useful for city/date event discovery and returns ticket URLs/status-like fields where available.

Implementation stance:

- Keep as first live event integration.
- Search by destination city and trip dates.
- Boost relevance with Spotify taste matches.
- Treat missing artists/venues as a reason to check secondary sources.

Source: https://developer.ticketmaster.com/products-and-docs/apis/discovery-api/v2/

### Spotify Web API

Spotify's top items endpoint returns current user's top artists/tracks and requires `user-top-read`; it supports `long_term`, `medium_term`, and `short_term` ranges, with limit up to 50. The followed-artists endpoint is also available in the Web API reference.

Implementation stance:

- Keep OAuth PKCE flow.
- Import top artists and followed artists into `MusicTasteProfile`.
- Use artist names and genres as search seeds for event providers.
- Avoid relying on popularity/genre fields as permanent contracts because Spotify marks some artist fields deprecated in the reference.

Sources:

- https://developer.spotify.com/documentation/web-api/reference/get-users-top-artists-and-tracks
- https://developer.spotify.com/documentation/web-api/reference/get-followed

### National Rail Darwin

National Rail describes Darwin as the GB rail industry's official train running information engine, with real-time arrivals/departures, platform numbers, delay estimates, schedule changes, and cancellations.

Implementation stance:

- Useful for travel-day reliability/disruption checks.
- Not a fare shopping API.
- Use later as a verification layer for Cheltenham Spa/Bristol/Birmingham rail legs.

Source: https://www.nationalrail.co.uk/developers/darwin-data-feeds/

### TransportAPI

TransportAPI presents managed UK transport data services covering rail, bus, journey planning, performance, and places.

Implementation stance:

- Candidate for Cheltenham-area bus/rail context and multimodal planning.
- Add only after cost/terms are acceptable.
- Keep manual estimates until the use case demands live local transport.

Source: https://www.transportapi.com/

### Trainline

Trainline's partner page describes affiliate links/widgets and distribution products, including a Global API and white-label solutions.

Implementation stance:

- Use manual/affiliate links for now.
- Do not depend on API access until accepted as a partner.

Source: https://www.thetrainline.com/about-us/affiliates

## Recommended Build Order

1. Keep calendar, Spotify, and Ticketmaster stable.
2. Add Amadeus auth and flight offer search adapters, but only write normalized `TransportOption` records.
3. Add Amadeus flight price confirmation and use it to raise booking confidence.
4. Add Amadeus hotel search for accommodation estimates.
5. Add source reliability scoring to recommendation reasons.
6. Add National Rail/TransportAPI only for disruption/local movement checks, not fare estimates.

## Guardrails

- Any provider result can enter `watch` or `research_needed`.
- `ready_to_verify` requires complete cost categories, currency conversion, calendar fit, and primary-source price/ticket verification.
- No Create Order, Hotel Booking, checkout, payment, or message sending without an explicit user request.
