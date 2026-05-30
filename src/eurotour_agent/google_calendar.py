from __future__ import annotations

import base64
import hashlib
import json
import secrets
from datetime import UTC, datetime, timedelta
from pathlib import Path
from urllib.parse import urlencode

import requests

from .models import BusyCalendarEvent, CalendarSnapshot

AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
FREEBUSY_URL = "https://www.googleapis.com/calendar/v3/freeBusy"
GOOGLE_CALENDAR_SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]


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
        "scope": " ".join(scopes or GOOGLE_CALENDAR_SCOPES),
        "state": pkce_state["state"],
        "code_challenge": pkce_state["code_challenge"],
        "code_challenge_method": "S256",
        "access_type": "offline",
        "prompt": "consent",
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
            "code": code,
            "code_verifier": code_verifier,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
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
    with path.open("w", encoding="utf-8") as handle:
        json.dump(token, handle, indent=2)
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
            raise ValueError("GOOGLE_CLIENT_ID is required to refresh an expired Google token.")
        token = refresh_access_token(client_id, token["refresh_token"])
        write_token(token_path, token)
    return token["access_token"]


def import_freebusy_snapshot(
    access_token: str,
    calendar_id: str,
    timezone: str,
    range_start: datetime,
    range_end: datetime,
) -> CalendarSnapshot:
    response = requests.post(
        FREEBUSY_URL,
        headers={"Authorization": f"Bearer {access_token}"},
        json={
            "timeMin": range_start.isoformat(),
            "timeMax": range_end.isoformat(),
            "timeZone": timezone,
            "items": [{"id": calendar_id}],
        },
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    busy_payload = payload.get("calendars", {}).get(calendar_id, {}).get("busy", [])
    busy_events = [
        BusyCalendarEvent(
            starts_at=datetime.fromisoformat(item["start"].replace("Z", "+00:00")),
            ends_at=datetime.fromisoformat(item["end"].replace("Z", "+00:00")),
            title="Busy",
            source="google_calendar_freebusy",
        )
        for item in busy_payload
    ]
    return CalendarSnapshot(
        timezone=timezone,
        range_start=range_start,
        range_end=range_end,
        busy_events=busy_events,
    )
