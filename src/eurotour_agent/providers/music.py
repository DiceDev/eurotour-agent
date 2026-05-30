from __future__ import annotations


class MusicTasteProvider:
    def list_priority_artists(self) -> list[str]:
        raise NotImplementedError

