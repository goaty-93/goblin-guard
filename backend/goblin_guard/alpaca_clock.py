from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class MarketClockUnavailable(RuntimeError):
    """Safe public error for the read-only Alpaca clock boundary."""


def _timestamp(value: Any, field: str) -> datetime:
    if not isinstance(value, str):
        raise MarketClockUnavailable(f"Alpaca market clock {field} is invalid")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise MarketClockUnavailable(f"Alpaca market clock {field} is invalid") from None
    if parsed.tzinfo is None:
        raise MarketClockUnavailable(f"Alpaca market clock {field} is invalid")
    return parsed.astimezone(timezone.utc)


@dataclass(frozen=True)
class MarketClock:
    timestamp: datetime
    is_open: bool
    next_open: datetime
    next_close: datetime

    def proposal_view(self) -> dict[str, str | bool]:
        return {
            "timestamp": self.timestamp.isoformat().replace("+00:00", "Z"),
            "is_open": self.is_open,
            "next_open": self.next_open.isoformat().replace("+00:00", "Z"),
            "next_close": self.next_close.isoformat().replace("+00:00", "Z"),
        }


@dataclass(frozen=True)
class AlpacaClockConfig:
    api_key: str
    api_secret: str
    base_url: str = "https://paper-api.alpaca.markets"
    timeout_seconds: float = 8.0

    def __post_init__(self) -> None:
        if not self.api_key or not self.api_secret:
            raise ValueError("Alpaca paper credentials are required")
        if self.base_url.rstrip("/") != "https://paper-api.alpaca.markets":
            raise ValueError("clock base URL must be https://paper-api.alpaca.markets")


class AlpacaClockClient:
    def __init__(self, config: AlpacaClockConfig, opener: Callable[..., Any] = urlopen):
        self.config = config
        self._opener = opener

    def fetch(self) -> MarketClock:
        request = Request(
            f"{self.config.base_url.rstrip('/')}/v2/clock",
            headers={"APCA-API-KEY-ID": self.config.api_key, "APCA-API-SECRET-KEY": self.config.api_secret, "Accept": "application/json"},
            method="GET",
        )
        try:
            with self._opener(request, timeout=self.config.timeout_seconds) as response:
                payload = json.load(response)
        except HTTPError as exc:
            raise MarketClockUnavailable(f"Alpaca market clock returned HTTP {exc.code}") from None
        except (URLError, TimeoutError, json.JSONDecodeError):
            raise MarketClockUnavailable("Alpaca market clock is unavailable") from None
        if not isinstance(payload, dict) or type(payload.get("is_open")) is not bool:
            raise MarketClockUnavailable("Alpaca market clock returned an invalid response")
        return MarketClock(
            _timestamp(payload.get("timestamp"), "timestamp"),
            payload["is_open"],
            _timestamp(payload.get("next_open"), "next_open"),
            _timestamp(payload.get("next_close"), "next_close"),
        )
