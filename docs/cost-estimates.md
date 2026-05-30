# Cost Estimates

Checked on 2026-05-30. Prices and API access rules change, because apparently computers were not enough trouble already.

## Recommended Starting Setup

Start with a local scheduled checker and no OpenAI API calls:

- Google Calendar: no additional API cost for normal personal usage, subject to quota.
- Spotify Web API: no per-call pricing found, but access/rate limits and developer-mode restrictions matter.
- Ticketmaster Discovery API: suitable first concert/events source if an API key is available.
- Flight data: use Amadeus or Skyscanner partner access where approved.
- Train data: start with manually tracked links and provider-specific APIs later; European rail data is fragmented.

## OpenAI Recommendation Cost

Official OpenAI API pricing page currently lists:

- `gpt-5-nano`: $0.05 / 1M input tokens, $0.005 / 1M cached input tokens, $0.40 / 1M output tokens.
- `gpt-5-mini`: $0.25 / 1M input tokens, $0.025 / 1M cached input tokens, $2.00 / 1M output tokens.
- `gpt-5-search-api`: $1.25 / 1M input tokens, $0.125 / 1M cached input tokens, $10.00 / 1M output tokens.

Source: https://platform.openai.com/docs/pricing/

## Practical Monthly OpenAI Scenarios

Assumptions:

- One recommendation run reads summarized calendar constraints, saved preferences, candidate transport/concert options, and prior trip state.
- A typical lightweight run uses about 8,000 input tokens and 1,500 output tokens.
- A heavier itinerary rebuild uses about 25,000 input tokens and 5,000 output tokens.
- Prices below use `gpt-5-mini`, not cached-input discounts.

| Scenario | Frequency | Estimated Tokens | Estimated AI Cost |
| --- | ---: | ---: | ---: |
| Manual planning only | 10 lightweight runs/month | 80k input, 15k output | ~$0.05/month |
| Daily travel scan summary | 30 lightweight runs/month | 240k input, 45k output | ~$0.15/month |
| Daily scan + weekly itinerary rebuild | 30 light + 4 heavy | 340k input, 65k output | ~$0.22/month |
| Aggressive monitoring | 8 light runs/day + 8 heavy/month | 2.12M input, 400k output | ~$1.33/month |

These estimates cover only OpenAI model tokens. They do not include hosting, paid travel-data APIs, SMS/email sending, proxy services, or web scraping infrastructure.

## Non-AI Provider Cost Notes

Google Calendar:

- Google states Calendar API use is available at no additional cost, with quota limits.
- Source: https://developers.google.com/calendar/api/guides/quota

Amadeus:

- Amadeus provides test and production environments. New apps get a free monthly request quota; production keeps the free quota and charges for additional calls.
- Source: https://developers.amadeus.com/self-service/apis-docs/guides/developer-guides/pricing/

Skyscanner:

- Skyscanner partner support says Travel APIs are free to use with no per-booking, yearly, or monthly fees, but access is partner/application based.
- Source: https://skyscannerpartnersupport.zendesk.com/hc/en-us/articles/4524639452573-How-much-does-it-cost-to-use-the-Skyscanner-Flights-API

Spotify:

- No per-call API pricing was found in official docs during this pass.
- Treat Spotify as access-limited rather than cost-limited. Build with caching and low polling.
- Watch for account, quota, and developer-mode restrictions.

Ticketmaster:

- Use as the first concert discovery integration if API key access is available.
- Confirm current API terms during implementation before relying on it for automation.

## Suggested Budget Guardrails

- Default OpenAI monthly cap: $10.
- Default model: `gpt-5-mini`.
- Use `gpt-5-nano` for classification, deduping, and cheap summaries.
- Cache stable context: preferences, home airports, blocked calendar windows, liked artists, and destination notes.
- Run transport/concert searches first; call the model only after there is something worth ranking.
- Store every run with estimated token usage and provider request counts.

## First Realistic Cost Target

For a personal v1 that checks once or twice per day and generates a few recommendation summaries per week:

- AI: under $1/month.
- Calendar and Spotify: likely $0 direct API cost.
- Concert discovery: likely $0 direct API cost if using approved/free sources.
- Flights: $0 during dev/test; production depends on provider approval and request volume.
- Hosting: $0 if local only, or a few dollars/month if hosted on a small scheduled worker.

