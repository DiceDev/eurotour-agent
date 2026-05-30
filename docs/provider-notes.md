# Provider Notes

## Google Calendar

Use OAuth and read-only access first. Write access should be added only after the agent can explain exactly what it will create or change.

Initial scopes:

- `https://www.googleapis.com/auth/calendar.readonly`

Current implementation uses Google OAuth for installed/native apps with PKCE, then Calendar API FreeBusy query to produce a local `CalendarSnapshot`.

Official docs:

- OAuth for installed/native apps: https://developers.google.com/identity/protocols/oauth2/native-app
- Calendar FreeBusy query: https://developers.google.com/workspace/calendar/api/v3/reference/freebusy/query

Later write scopes:

- `https://www.googleapis.com/auth/calendar.events`

## Spotify

Use Spotify OAuth to read followed artists, top artists, saved tracks, and playlists where available. Cache aggressively and avoid frequent polling.

Useful data:

- Followed artists.
- Top artists.
- Saved albums/tracks.
- Playlists with artist names.

V1 implementation uses Spotify Authorization Code with PKCE and the scopes `user-top-read` and `user-follow-read`. The imported taste profile stores artist names, Spotify IDs, genres, popularity, and weights, then boosts matching concert relevance.

Official docs:

- Authorization and OAuth flows: https://developer.spotify.com/documentation/web-api/concepts/authorization
- PKCE flow: https://developer.spotify.com/documentation/web-api/tutorials/code-pkce-flow
- Scopes: https://developer.spotify.com/documentation/web-api/concepts/scopes
- Top artists/tracks: https://developer.spotify.com/documentation/web-api/reference/get-users-top-artists-and-tracks
- Followed artists: https://developer.spotify.com/documentation/web-api/reference/get-followed

## Concerts

Start with Ticketmaster Discovery API and supplement with venue/artist links as needed. Bandsintown, Songkick, and direct venue calendars are possible later integrations depending on API access.

## Flights

Start with Amadeus self-service APIs for development. Skyscanner is attractive if partner access is approved.

For manual and chat-operated work, use the flight search stack in [flight-booking-playbook.md](flight-booking-playbook.md). The core rule is simple: discover broadly, verify on the airline site, and evaluate total trip cost rather than headline fare.

## Trains

European train pricing is fractured. Start by storing watched routes and links, then add APIs per region/provider where available.

Candidate sources:

- Deutsche Bahn for Germany/international routes.
- SNCF/Trainline-style sources where accessible.
- National operator APIs for specific countries.

## Concerts

Use the concert discovery stack in [concert-discovery-playbook.md](concert-discovery-playbook.md). The strongest v1 mix is Spotify/Bandsintown for taste, Ticketmaster/Songkick for structured search, Resident Advisor/DICE for scene discovery, and venue calendars for the stuff algorithms miss.

Current structured provider:

- Ticketmaster Discovery search via `ticketmaster-search`, gated by `TICKETMASTER_API_KEY`.

## Accommodation and Ground Transport

Use [accommodation-and-ground-transport-playbook.md](accommodation-and-ground-transport-playbook.md). V1 should treat lodging, buses/coaches, local transit, food/drink, and buffers as first-class cost components so reports estimate the whole trip rather than just the glamorous bits.
