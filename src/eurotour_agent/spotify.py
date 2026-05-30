from __future__ import annotations

import base64
import hashlib
import json
import secrets
from datetime import UTC, datetime, timedelta
from pathlib import Path
from urllib.parse import urlencode

import requests

from .models import MusicTasteArtist, MusicTasteProfile

AUTH_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"
API_BASE_URL = "https://api.spotify.com/v1"
SPOTIFY_SCOPES = ["user-top-read", "user-follow-read"]


def create_pkce_state() -> dict[str, str]:
    verifier = secrets.token_urlsafe(64)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode("ascii")).digest()).decode("ascii").rstrip("=")
    return {
        "code_verifier": verifier,
        "code_challenge": challenge,
        "state": secrets.token_urlsafe(24),
    }


def build_authorization_url(
    client_id: str,
    redirect_uri: str,
    pkce_state: dict[str, str],
    scopes: list[str] | None = None,
) -> str:
    params = {
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "scope": " ".join(scopes or SPOTIFY_SCOPES),
        "state": pkce_state["state"],
        "code_challenge_method": "S256",
        "code_challenge": pkce_state["code_challenge"],
    }
    return f"{AUTH_URL}?{urlencode(params)}"


def exchange_code_for_token(
    client_id: str,
    redirect_uri: str,
    code: str,
    code_verifier: str,
) -> dict:
    response = requests.post(
        TOKEN_URL,
        data={
            "client_id": client_id,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "code_verifier": code_verifier,
        },
        timeout=30,
    )
    response.raise_for_status()
    token = response.json()
    token["obtained_at"] = datetime.now(UTC).isoformat()
    return token


def refresh_access_token(client_id: str, refresh_token: str) -> dict:
    response = requests.post(
        TOKEN_URL,
        data={
            "client_id": client_id,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        },
        timeout=30,
    )
    response.raise_for_status()
    token = response.json()
    token["obtained_at"] = datetime.now(UTC).isoformat()
    if "refresh_token" not in token:
        token["refresh_token"] = refresh_token
    return token


def load_token(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_token(path: Path, token: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    safe_token = dict(token)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(safe_token, handle, indent=2)
        handle.write("\n")


def token_is_expired(token: dict, skew_seconds: int = 120) -> bool:
    obtained_at = token.get("obtained_at")
    expires_in = token.get("expires_in")
    if not obtained_at or not expires_in:
        return True
    obtained = datetime.fromisoformat(obtained_at)
    if obtained.tzinfo is None:
        obtained = obtained.replace(tzinfo=UTC)
    return datetime.now(UTC) >= obtained + timedelta(seconds=int(expires_in) - skew_seconds)


def get_valid_access_token(client_id: str | None, token_path: Path) -> str:
    token = load_token(token_path)
    if token_is_expired(token):
        if not client_id:
            raise ValueError("SPOTIFY_CLIENT_ID is required to refresh an expired Spotify token.")
        token = refresh_access_token(client_id, token["refresh_token"])
        write_token(token_path, token)
    return token["access_token"]


def import_music_taste(access_token: str, top_limit: int = 50, followed_limit: int = 50) -> MusicTasteProfile:
    top_artists = _get_top_artists(access_token=access_token, limit=top_limit)
    followed_artists = _get_followed_artists(access_token=access_token, limit=followed_limit)
    artists_by_id: dict[str, MusicTasteArtist] = {}

    for index, artist in enumerate(top_artists):
        spotify_id = artist["id"]
        artists_by_id[spotify_id] = MusicTasteArtist(
            name=artist["name"],
            source="spotify_top_artists",
            spotify_id=spotify_id,
            genres=artist.get("genres", []),
            popularity=artist.get("popularity"),
            weight=max(0.45, 1.0 - index / max(len(top_artists), 1) * 0.45),
        )

    for artist in followed_artists:
        spotify_id = artist["id"]
        existing = artists_by_id.get(spotify_id)
        if existing:
            existing.weight = min(1.0, existing.weight + 0.1)
            continue
        artists_by_id[spotify_id] = MusicTasteArtist(
            name=artist["name"],
            source="spotify_followed_artists",
            spotify_id=spotify_id,
            genres=artist.get("genres", []),
            popularity=artist.get("popularity"),
            weight=0.65,
        )

    genre_weights: dict[str, float] = {}
    for artist in artists_by_id.values():
        for genre in artist.genres:
            genre_weights[genre] = genre_weights.get(genre, 0.0) + artist.weight

    genres = [
        genre
        for genre, _ in sorted(genre_weights.items(), key=lambda item: item[1], reverse=True)[:25]
    ]

    return MusicTasteProfile(
        generated_at=datetime.now(UTC),
        source="spotify",
        artists=sorted(artists_by_id.values(), key=lambda item: item.weight, reverse=True),
        genres=genres,
    )


def _get_top_artists(access_token: str, limit: int) -> list[dict]:
    response = requests.get(
        f"{API_BASE_URL}/me/top/artists",
        headers={"Authorization": f"Bearer {access_token}"},
        params={"time_range": "medium_term", "limit": min(limit, 50)},
        timeout=30,
    )
    response.raise_for_status()
    return response.json().get("items", [])


def _get_followed_artists(access_token: str, limit: int) -> list[dict]:
    artists: list[dict] = []
    after = None
    followed_limit = limit
    while len(artists) < followed_limit:
        page_limit = min(50, followed_limit - len(artists))
        params = {"type": "artist", "limit": page_limit}
        if after:
            params["after"] = after
        response = requests.get(
            f"{API_BASE_URL}/me/following",
            headers={"Authorization": f"Bearer {access_token}"},
            params=params,
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json().get("artists", {})
        artists.extend(payload.get("items", []))
        cursors = payload.get("cursors") or {}
        after = cursors.get("after")
        if not after or not payload.get("next"):
            break
    return artists
