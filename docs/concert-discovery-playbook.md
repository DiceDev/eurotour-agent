# Concert Discovery Playbook

Research checked on 2026-05-30.

## Default Discovery Stack

Use several sources because no single concert database is complete:

1. Spotify Live Events for personalized artist and venue discovery.
2. Bandsintown for artist tracking and broad concert alerts.
3. Songkick for artist/city tracking and API-friendly event data.
4. Ticketmaster Discovery API for structured event search by city/date/category.
5. DICE for club, indie, and curated city listings, especially where it is active.
6. Resident Advisor for electronic music, club nights, and festivals.
7. Venue calendars and artist mailing lists for early announcements and presales.

Sources:

- Spotify Live Events for Artists: https://artists.spotify.com/live-events
- Spotify venue-following announcement: https://newsroom.spotify.com/2025-10-20/live-music-venues-on-spotify/
- Bandsintown API docs: https://help.artists.bandsintown.com/en/articles/9186477-api-documentation
- Bandsintown distribution to Spotify/Google/Apple/Shazam: https://help.artists.bandsintown.com/en/articles/10518205-distribution-to-spotify-google-apple-and-shazam
- Songkick API docs: https://www.songkick.com/developer/getting-started
- Ticketmaster Discovery API: https://developer.ticketmaster.com/products-and-docs/apis/discovery-manual/v2/
- DICE Spotify/Apple Music sync help: https://dicefm.zendesk.com/hc/en-gb/articles/22365422759313-Getting-started-with-DICE
- Eventbrite API docs: https://www.eventbrite.com/platform/docs/events

## Discovery Rules

- Artist-first search catches direct tour dates.
- City/date search catches festivals, support slots, and venues you did not know to follow.
- Venue-following catches smaller shows before algorithms bother with them.
- Ticketing-platform search catches shows that never surface cleanly in music apps.
- Mailing lists and artist socials still matter for presales. Horrifying, but true.

## Europe Source Notes

- Spotify: good for personalized recommendations and now venue following, but do not rely on it as the only source.
- Bandsintown: strong artist tracking and distribution; Spotify uses Bandsintown data for event listings.
- Songkick: useful API path for artist/event data.
- Ticketmaster: strong where Ticketmaster has coverage; structured API supports music classification, city, date, venue, and attraction searches.
- DICE: valuable for London and other active cities; syncs Spotify or Apple Music to personalize recommendations.
- Resident Advisor: essential for electronic music, clubs, DJs, and festivals.
- Eventbrite: useful for independent events, small promoters, and oddball nights, but search quality varies.
- Venue calendars: best source for small rooms, local promoters, and newly announced shows.

## Search Patterns

For a city/date window:

1. Search Ticketmaster by city, date range, and music classification.
2. Search Songkick by city/metro area if available.
3. Search Bandsintown for priority artists.
4. Check Spotify Live Events for the city and followed/favorite artists.
5. Check DICE and Resident Advisor for the city.
6. Check top venue calendars for the genre.
7. Normalize duplicates by artist, date, city, venue, and ticket URL.

For an artist:

1. Artist website tour page.
2. Spotify artist page and Live Events.
3. Bandsintown artist events.
4. Songkick artist events.
5. Ticketmaster attraction search.
6. Venue/promoter pages for missing support acts or presales.

## Relevance Scoring

Score an event by:

- Artist priority.
- Genre fit.
- Venue quality.
- Date/calendar fit.
- Ticket availability.
- Ticket price.
- City/trip fit.
- Rarity: one-off, festival, reunion, small venue, likely sellout.

Suggested weights:

- 35% music taste match.
- 20% calendar/trip fit.
- 15% venue/city value.
- 15% ticket confidence and price.
- 15% rarity/urgency.

## Alert Rules

Escalate immediately when:

- A priority artist announces Europe dates.
- A good event overlaps a cheap travel window.
- A small venue show by a liked artist appears.
- Ticket status changes from unavailable/waitlist to available.
- A festival lineup adds multiple liked artists.

Ignore or down-rank:

- Stub resale spam unless primary tickets are gone and the event is high priority.
- Events without a confirmed venue/date.
- DJ nights with vague lineups unless the venue/promoter is trusted.
- Events that require brutal travel for mediocre fit.

## What The Agent Should Record

For every candidate event:

- Artist/event name.
- Venue.
- City.
- Date and local time.
- Source.
- Ticket URL.
- Primary/resale status if known.
- Price and fees if known.
- Relevance reason.
- Trip(s) it could anchor.
- Last checked timestamp.

