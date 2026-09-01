from datetime import datetime, timezone
import io
import json
import unittest
from urllib.error import HTTPError

from goblin_guard import AlpacaMarketDataClient, AlpacaMarketDataConfig, EvidenceValidationError, MarketDataUnavailable, build_evidence_packet


NOW = datetime(2026, 8, 28, 15, 0, tzinfo=timezone.utc)
BARS = [
    {"t":"2026-08-28T14:58:00Z","o":190.0,"h":191.0,"l":189.5,"c":190.5,"v":1200,"n":45,"vw":190.4},
    {"t":"2026-08-28T14:59:00Z","o":190.5,"h":192.0,"l":190.2,"c":191.8,"v":1700,"n":61,"vw":191.4},
]


class Response(io.BytesIO):
    def __enter__(self): return self
    def __exit__(self, *args): self.close()


class EvidenceTests(unittest.TestCase):
    def test_packet_has_deterministic_content_addressed_id(self):
        first = build_evidence_packet(symbol="AAPL", feed="iex", fetched_at=NOW, raw_bars=BARS)
        second = build_evidence_packet(symbol="AAPL", feed="iex", fetched_at=NOW, raw_bars=BARS)
        self.assertEqual(first.evidence_id, second.evidence_id)
        self.assertEqual(first.as_of.isoformat(), "2026-08-28T14:59:00+00:00")
        self.assertEqual(first.proposal_view()["bars"][-1]["close"], "191.8")

    def test_evidence_id_survives_json_round_trip(self):
        first = build_evidence_packet(symbol="AAPL",feed="iex",fetched_at=NOW,raw_bars=BARS)
        view = json.loads(json.dumps(first.proposal_view()))
        rebuilt = [{"t":b["timestamp"],"o":b["open"],"h":b["high"],"l":b["low"],"c":b["close"],"v":b["volume"],"n":b["trade_count"],"vw":b["vwap"]} for b in view["bars"]]
        second = build_evidence_packet(symbol="AAPL",feed="iex",fetched_at=NOW,raw_bars=rebuilt)
        self.assertEqual(first.evidence_id,second.evidence_id)

    def test_malformed_ohlc_is_rejected(self):
        malformed = [{**BARS[0], "l": 200.0}]
        with self.assertRaises(EvidenceValidationError):
            build_evidence_packet(symbol="AAPL", feed="iex", fetched_at=NOW, raw_bars=malformed)

    def test_unsorted_bars_are_rejected(self):
        with self.assertRaises(EvidenceValidationError):
            build_evidence_packet(symbol="AAPL", feed="iex", fetched_at=NOW, raw_bars=reversed(BARS))

    def test_client_sends_read_only_request_and_normalizes_response(self):
        seen = {}
        def opener(request, timeout):
            seen.update(url=request.full_url, headers=dict(request.header_items()), method=request.get_method(), timeout=timeout)
            return Response(json.dumps({"bars":BARS,"symbol":"AAPL","next_page_token":None}).encode())
        client = AlpacaMarketDataClient(AlpacaMarketDataConfig("test-key","test-secret"), opener)
        packet = client.fetch_recent_bars("AAPL", now=NOW, minimum_bars=2)
        self.assertEqual(seen["method"], "GET")
        self.assertIn("/v2/stocks/AAPL/bars?", seen["url"])
        self.assertIn("feed=iex", seen["url"])
        self.assertNotIn("test-secret", seen["url"])
        self.assertEqual(packet.source, "alpaca_market_data_v2")

    def test_http_errors_are_redacted(self):
        def opener(request, timeout):
            raise HTTPError(request.full_url, 401, "contains-secret", {}, None)
        client = AlpacaMarketDataClient(AlpacaMarketDataConfig("test-key","test-secret"), opener)
        with self.assertRaisesRegex(MarketDataUnavailable, "HTTP 401") as caught:
            client.fetch_recent_bars("AAPL", now=NOW)
        self.assertNotIn("test-secret", str(caught.exception))

    def test_empty_current_window_falls_back_to_recent_trading_bars(self):
        seen = []
        def opener(request, timeout):
            seen.append(request.full_url)
            if len(seen) == 1:
                return Response(json.dumps({"bars":None,"symbol":"AAPL","next_page_token":None}).encode())
            return Response(json.dumps({"bars":list(reversed(BARS)),"symbol":"AAPL","next_page_token":None}).encode())
        packet = AlpacaMarketDataClient(AlpacaMarketDataConfig("key","secret"), opener).fetch_recent_bars("AAPL",now=NOW,minimum_bars=2)
        self.assertEqual(len(seen),2)
        self.assertIn("sort=desc",seen[1])
        self.assertEqual(packet.bars[0].timestamp.isoformat(),"2026-08-28T14:58:00+00:00")
        self.assertEqual(packet.bars[-1].timestamp.isoformat(),"2026-08-28T14:59:00+00:00")

    def test_partial_opening_window_falls_back_for_indicator_warmup(self):
        seen = []
        history = []
        for index in range(30):
            minute = index + 1
            history.append({"t":f"2026-08-28T14:{minute:02d}:00Z","o":190.0,"h":191.0,"l":189.0,"c":190.5,"v":1200,"n":45,"vw":190.4})
        def opener(request, timeout):
            seen.append(request.full_url)
            if len(seen) == 1:
                return Response(json.dumps({"bars":history[-12:],"symbol":"AAPL","next_page_token":None}).encode())
            return Response(json.dumps({"bars":list(reversed(history)),"symbol":"AAPL","next_page_token":None}).encode())
        packet = AlpacaMarketDataClient(AlpacaMarketDataConfig("key","secret"),opener).fetch_recent_bars("AAPL",now=NOW)
        self.assertEqual(len(seen),2)
        self.assertIn("sort=desc",seen[1])
        self.assertEqual(len(packet.bars),30)
        self.assertEqual(packet.as_of.isoformat(),"2026-08-28T14:30:00+00:00")

    def test_fallback_with_insufficient_history_fails_closed(self):
        def opener(request, timeout):
            return Response(json.dumps({"bars":BARS,"symbol":"AAPL","next_page_token":None}).encode())
        client = AlpacaMarketDataClient(AlpacaMarketDataConfig("key","secret"),opener)
        with self.assertRaisesRegex(MarketDataUnavailable,"fewer than 21"):
            client.fetch_recent_bars("AAPL",now=NOW)

    def test_base_url_is_pinned(self):
        with self.assertRaises(ValueError):
            AlpacaMarketDataConfig("key", "secret", base_url="https://example.com")


if __name__ == "__main__":
    unittest.main()
