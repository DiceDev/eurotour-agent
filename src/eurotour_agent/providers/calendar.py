from __future__ import annotations

from datetime import datetime

from eurotour_agent.models import CalendarWindow


class CalendarProvider:
    def list_free_windows(self, starts_at: datetime, ends_at: datetime) -> list[CalendarWindow]:
        raise NotImplementedError

