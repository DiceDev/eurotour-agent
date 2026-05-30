from __future__ import annotations

from datetime import date

from eurotour_agent.models import TransportOption


class TransportProvider:
    def search(self, origin: str, destination: str, starts_on: date, ends_on: date) -> list[TransportOption]:
        raise NotImplementedError

