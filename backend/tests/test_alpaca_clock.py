from io import BytesIO
import unittest
from urllib.error import HTTPError

from goblin_guard.alpaca_clock import AlpacaClockClient, AlpacaClockConfig, MarketClockUnavailable


class Response(BytesIO):
    def __enter__(self): return self
    def __exit__(self, *args): self.close()


class ClockTests(unittest.TestCase):
    def test_fetches_and_normalizes_read_only_clock(self):
        seen = {}
        def opener(request, timeout):
            seen["request"] = request
            return Response(b'{"timestamp":"2026-08-28T14:00:00-04:00","is_open":true,"next_open":"2026-08-31T09:30:00-04:00","next_close":"2026-08-28T16:00:00-04:00"}')
        clock = AlpacaClockClient(AlpacaClockConfig("key","secret"),opener).fetch()
        self.assertTrue(clock.is_open)
        self.assertEqual(seen["request"].full_url,"https://paper-api.alpaca.markets/v2/clock")
        self.assertEqual(seen["request"].method,"GET")
        self.assertEqual(clock.timestamp.isoformat(),"2026-08-28T18:00:00+00:00")

    def test_invalid_shape_fails_closed(self):
        with self.assertRaises(MarketClockUnavailable):
            AlpacaClockClient(AlpacaClockConfig("key","secret"),lambda *_args,**_kwargs: Response(b'{"is_open":"yes"}')).fetch()

    def test_http_error_is_redacted(self):
        def opener(*_args,**_kwargs): raise HTTPError("https://safe",401,"bad",{},None)
        with self.assertRaisesRegex(MarketClockUnavailable,"HTTP 401"):
            AlpacaClockClient(AlpacaClockConfig("key","secret"),opener).fetch()

    def test_rejects_non_paper_host(self):
        with self.assertRaises(ValueError): AlpacaClockConfig("key","secret","https://api.alpaca.markets")


if __name__ == "__main__": unittest.main()
