from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import json
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .evidence import EvidencePacket, EvidenceValidationError, build_evidence_packet


class MarketDataUnavailable(RuntimeError):
    """Safe public error for upstream authentication, transport, or shape failures."""


@dataclass(frozen=True)
class AlpacaMarketDataConfig:
    api_key: str
    api_secret: str
    base_url: str = "https://data.alpaca.markets"
    feed: str = "iex"
    timeout_seconds: float = 8.0

    def __post_init__(self) -> None:
        if not self.api_key or not self.api_secret:
            raise ValueError("Alpaca market-data credentials are required")
        if self.base_url.rstrip("/") != "https://data.alpaca.markets":
            raise ValueError("market-data base URL must be https://data.alpaca.markets")
        if self.feed not in {"iex", "sip", "delayed_sip"}:
            raise ValueError("unsupported stock feed")


class AlpacaMarketDataClient:
    def __init__(self, config: AlpacaMarketDataConfig, opener: Callable[..., Any] = urlopen):
        self.config = config
        self._opener = opener

    def fetch_recent_bars(self, symbol: str, *, now: datetime | None = None, minutes: int = 30) -> EvidencePacket:
        if not symbol.isascii() or not symbol.isupper() or not symbol.replace(".", "").isalnum():
            raise ValueError("symbol must be an uppercase ticker")
        if not 5 <= minutes <= 240:
            raise ValueError("minutes must be between 5 and 240")
        fetched_at = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
        start = fetched_at - timedelta(minutes=minutes)
        params = urlencode({"timeframe":"1Min","start":start.isoformat().replace("+00:00","Z"),"end":fetched_at.isoformat().replace("+00:00","Z"),"limit":minutes,"adjustment":"raw","feed":self.config.feed,"sort":"asc"})
        url = f"{self.config.base_url.rstrip('/')}/v2/stocks/{symbol}/bars?{params}"
        request = Request(url, headers={"APCA-API-KEY-ID":self.config.api_key,"APCA-API-SECRET-KEY":self.config.api_secret,"Accept":"application/json"})
        try:
            with self._opener(request, timeout=self.config.timeout_seconds) as response:
                payload = json.load(response)
        except HTTPError as exc:
            raise MarketDataUnavailable(f"Alpaca market data returned HTTP {exc.code}") from None
        except (URLError, TimeoutError, json.JSONDecodeError):
            raise MarketDataUnavailable("Alpaca market data is unavailable") from None
        if not isinstance(payload, dict) or not isinstance(payload.get("bars"), list):
            raise MarketDataUnavailable("Alpaca market data returned an invalid response")
        try:
            return build_evidence_packet(symbol=symbol, feed=self.config.feed, fetched_at=fetched_at, raw_bars=payload["bars"])
        except EvidenceValidationError as exc:
            raise MarketDataUnavailable(f"Alpaca evidence rejected: {exc}") from None
