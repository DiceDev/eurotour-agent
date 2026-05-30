from __future__ import annotations

from datetime import date

from eurotour_agent.models import EventOption


class ConcertProvider:
    def search_events(self, city: str, starts_on: date, ends_on: date) -> list[EventOption]:
        raise NotImplementedError

