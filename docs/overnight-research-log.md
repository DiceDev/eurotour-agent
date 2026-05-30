# Overnight Research Log

Date: 2026-05-30

Scope: provider research and low-risk implementation work for the Europe travel/music agent. The pass focused on provider selection, Amadeus scaffolding, Cheltenham routing, and local automation that does not spend money, book travel, or send messages automatically.

## Completed

- Added provider decision matrix and readiness checks.
- Added Amadeus Flight Offers Search adapter.
- Added Amadeus Hotel Offers adapter.
- Added Cheltenham-aware route seed generation.
- Added source reliability scoring to monitoring briefs.
- Added notification digest and price-observation extraction in earlier slices.

## Source Findings

### Amadeus

Use Amadeus as the first flight and hotel API candidate because it exposes structured self-service travel APIs and separates search from confirmation/booking. For flights, use Flight Offers Search for candidate fares and Flight Offers Price before treating an offer as current. For hotels, use hotel list/search/offer endpoints for availability and estimates, but keep booking out of scope.

Source:

- https://developers.amadeus.com/self-service/apis-docs/guides/developer-guides/resources/flights/
- https://developers.amadeus.com/self-service/apis-docs/guides/developer-guides/resources/hotels/

### Ticketmaster

Ticketmaster Discovery remains the best first structured event provider already represented in the app. It should be supplemented by venue calendars and secondary event sources because smaller or independent music acts may not appear there.

Source:

- https://developer.ticketmaster.com/products-and-docs/apis/discovery-api/v2/

### Spotify

Spotify stays as the music-taste source. Top artists/followed artists are useful search seeds for Ticketmaster and later secondary event providers.

Source:

- https://developer.spotify.com/documentation/web-api/reference/get-users-top-artists-and-tracks
- https://developer.spotify.com/documentation/web-api/reference/get-followed

### UK Rail And Ground Transport

National Rail Darwin is official and reliable for GB train running/disruption data, but not fare shopping. TransportAPI is the best candidate for managed UK rail/bus/multimodal data if cost and terms work for personal use.

Sources:

- https://www.nationalrail.co.uk/developers/darwin-data-feeds/
- https://www.transportapi.com/

## Current Commands To Try

```powershell
python -m eurotour_agent.scheduler provider-readiness --markdown
python -m eurotour_agent.scheduler route-seeds --output local\route_seeds.yaml
python -m eurotour_agent.scheduler amadeus-flight-search BRS BER --departure-date 2026-07-03 --return-date 2026-07-06
python -m eurotour_agent.scheduler amadeus-hotel-offers HLPAR266 --check-in-date 2026-07-03 --check-out-date 2026-07-06
```

The Amadeus commands require `AMADEUS_CLIENT_ID` and `AMADEUS_CLIENT_SECRET`.

## Next Build Queue

1. Add Amadeus Flight Offers Price confirmation support.
2. Add a city-to-Amadeus-hotel-ID discovery command so hotel searches do not require manual hotel IDs.
3. Add route-seed-to-Amadeus-flight-search orchestration for all airport pairs.
4. Add provider result freshness checks to `audit-run`.
5. Add a secondary event-source research pass focused on Bandsintown, Songkick, DICE, Resident Advisor, and venue calendars.
6. Add optional notification sending only after digest review is solid.

## Guardrails

- Do not use flight order creation or hotel booking APIs.
- Do not automatically send notifications until explicitly requested.
- Treat every provider price as advisory until primary-source verification.
- Keep private provider outputs under `local/`.
