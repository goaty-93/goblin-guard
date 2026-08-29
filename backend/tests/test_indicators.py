from datetime import datetime, timedelta, timezone
from decimal import Decimal
import unittest

from goblin_guard.evidence import MarketBar
from goblin_guard.indicators import IndicatorUnavailable, calculate_indicators


def bars(count: int, step: Decimal = Decimal("1")) -> tuple[MarketBar, ...]:
    start = datetime(2026, 8, 28, 13, 0, tzinfo=timezone.utc)
    result = []
    for index in range(count):
        close = Decimal("100") + (step * index)
        result.append(MarketBar(start + timedelta(minutes=index), close - 1, close + 1, close - 2, close, 100 + index, 10, close))
    return tuple(result)


class IndicatorTests(unittest.TestCase):
    def test_calculates_deterministic_metrics_from_validated_bars(self):
        result = calculate_indicators(bars(21))
        self.assertEqual(result.ema20, Decimal("110.50"))
        self.assertEqual(result.rsi14, Decimal("100.00"))
        self.assertEqual(result.atr14, Decimal("3.00"))
        self.assertEqual(result.volume_ratio20, Decimal("1.10"))

    def test_flat_series_has_neutral_rsi(self):
        self.assertEqual(calculate_indicators(bars(21, Decimal("0"))).rsi14, Decimal("50.00"))

    def test_insufficient_history_fails_closed(self):
        with self.assertRaises(IndicatorUnavailable): calculate_indicators(bars(20))


if __name__ == "__main__": unittest.main()
