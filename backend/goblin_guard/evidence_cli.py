from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys

from .alpaca_market_data import AlpacaMarketDataClient, AlpacaMarketDataConfig, MarketDataUnavailable
from .evidence import build_evidence_packet


def _synthetic_packet(symbol: str):
    fixture_path = Path(__file__).resolve().parents[1] / "fixtures" / "alpaca-bars-aapl.json"
    payload = json.loads(fixture_path.read_text(encoding="utf-8"))
    if symbol != payload["symbol"]:
        raise ValueError(f"synthetic fixture is only available for {payload['symbol']}")
    return build_evidence_packet(
        symbol=symbol,
        feed="synthetic",
        fetched_at=datetime(2026, 8, 28, 15, 0, tzinfo=timezone.utc),
        raw_bars=payload["bars"],
        source="synthetic_demo_fixture",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a read-only Goblin Guard evidence packet.")
    parser.add_argument("symbol", nargs="?", default="AAPL")
    parser.add_argument("--synthetic", action="store_true", help="Use the committed credential-free fixture.")
    args = parser.parse_args(argv)
    symbol = args.symbol.upper()
    if args.synthetic:
        try:
            packet = _synthetic_packet(symbol)
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 2
        mode = "synthetic"
    else:
        key = os.getenv("ALPACA_API_KEY", "")
        secret = os.getenv("ALPACA_API_SECRET", "")
        if not key or not secret:
            print("Live market data is disabled: set ALPACA_API_KEY and ALPACA_API_SECRET, or use --synthetic.", file=sys.stderr)
            return 2
        try:
            packet = AlpacaMarketDataClient(AlpacaMarketDataConfig(key, secret)).fetch_recent_bars(symbol)
        except MarketDataUnavailable as exc:
            print(str(exc), file=sys.stderr)
            return 1
        mode = "live_read_only"
    print(json.dumps({"mode": mode, "order_submission": "disabled", "evidence": packet.proposal_view()}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
