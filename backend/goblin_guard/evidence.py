from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import json
from typing import Any, Iterable


class EvidenceValidationError(ValueError):
    """Raised when upstream market data cannot form trusted evidence."""


def _decimal(value: Any, field: str) -> Decimal:
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        raise EvidenceValidationError(f"{field} must be numeric") from None
    if not result.is_finite():
        raise EvidenceValidationError(f"{field} must be finite")
    return result


def _timestamp(value: Any) -> datetime:
    if not isinstance(value, str):
        raise EvidenceValidationError("bar timestamp must be a string")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise EvidenceValidationError("bar timestamp must be ISO-8601") from None
    if parsed.tzinfo is None:
        raise EvidenceValidationError("bar timestamp must include a timezone")
    return parsed.astimezone(timezone.utc)


@dataclass(frozen=True)
class MarketBar:
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int
    trade_count: int
    vwap: Decimal

    @classmethod
    def from_alpaca(cls, payload: Any) -> "MarketBar":
        if not isinstance(payload, dict):
            raise EvidenceValidationError("bar must be an object")
        required = {"t", "o", "h", "l", "c", "v", "n", "vw"}
        missing = required - set(payload)
        if missing:
            raise EvidenceValidationError(f"bar missing fields: {sorted(missing)}")
        bar = cls(
            timestamp=_timestamp(payload["t"]),
            open=_decimal(payload["o"], "open"),
            high=_decimal(payload["h"], "high"),
            low=_decimal(payload["l"], "low"),
            close=_decimal(payload["c"], "close"),
            volume=int(payload["v"]),
            trade_count=int(payload["n"]),
            vwap=_decimal(payload["vw"], "vwap"),
        )
        if min(bar.open, bar.high, bar.low, bar.close, bar.vwap) <= 0:
            raise EvidenceValidationError("bar prices must be positive")
        if bar.low > min(bar.open, bar.close) or bar.high < max(bar.open, bar.close) or bar.low > bar.high:
            raise EvidenceValidationError("bar OHLC values are inconsistent")
        if bar.volume < 0 or bar.trade_count < 0:
            raise EvidenceValidationError("bar activity cannot be negative")
        return bar


@dataclass(frozen=True)
class EvidencePacket:
    evidence_id: str
    symbol: str
    feed: str
    source: str
    fetched_at: datetime
    as_of: datetime
    bars: tuple[MarketBar, ...]

    def proposal_view(self) -> dict[str, Any]:
        """Return the compact, immutable view permitted at the AI boundary."""
        return {
            "evidence_id": self.evidence_id,
            "symbol": self.symbol,
            "feed": self.feed,
            "source": self.source,
            "fetched_at": self.fetched_at.isoformat().replace("+00:00", "Z"),
            "as_of": self.as_of.isoformat().replace("+00:00", "Z"),
            "bars": [
                {
                    "timestamp": bar.timestamp.isoformat().replace("+00:00", "Z"),
                    "open": str(bar.open), "high": str(bar.high), "low": str(bar.low),
                    "close": str(bar.close), "volume": bar.volume,
                    "trade_count": bar.trade_count, "vwap": str(bar.vwap),
                }
                for bar in self.bars
            ],
        }


def build_evidence_packet(*, symbol: str, feed: str, fetched_at: datetime, raw_bars: Iterable[Any], source: str = "alpaca_market_data_v2") -> EvidencePacket:
    if fetched_at.tzinfo is None:
        raise EvidenceValidationError("fetched_at must include a timezone")
    raw_items = tuple(raw_bars)
    bars = tuple(MarketBar.from_alpaca(item) for item in raw_items)
    if not bars:
        raise EvidenceValidationError("at least one bar is required")
    if tuple(sorted(bar.timestamp for bar in bars)) != tuple(bar.timestamp for bar in bars):
        raise EvidenceValidationError("bars must be sorted oldest to newest")
    canonical_bars = [
        {"timestamp":bar.timestamp.isoformat(),"open":str(bar.open),"high":str(bar.high),"low":str(bar.low),"close":str(bar.close),"volume":bar.volume,"trade_count":bar.trade_count,"vwap":str(bar.vwap)}
        for bar in bars
    ]
    canonical = json.dumps({"symbol": symbol, "feed": feed, "source": source, "bars": canonical_bars}, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]
    return EvidencePacket(f"bars:{symbol}:{bars[-1].timestamp.strftime('%Y%m%dT%H%M%SZ')}:{digest}", symbol, feed, source, fetched_at.astimezone(timezone.utc), bars[-1].timestamp, bars)
