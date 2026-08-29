from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from .evidence import MarketBar


class IndicatorUnavailable(ValueError):
    """Raised when validated bars are insufficient for deterministic indicators."""


@dataclass(frozen=True)
class TechnicalIndicators:
    ema20: Decimal
    rsi14: Decimal
    atr14: Decimal
    volume_ratio20: Decimal

    def proposal_view(self) -> dict[str, str]:
        return {
            "ema20": str(self.ema20),
            "rsi14": str(self.rsi14),
            "atr14": str(self.atr14),
            "volume_ratio20": str(self.volume_ratio20),
        }


def calculate_indicators(bars: tuple[MarketBar, ...]) -> TechnicalIndicators:
    if len(bars) < 21:
        raise IndicatorUnavailable("at least 21 validated bars are required")

    closes = [bar.close for bar in bars]
    alpha = Decimal(2) / Decimal(21)
    ema = sum(closes[:20]) / Decimal(20)
    for close in closes[20:]:
        ema = (close * alpha) + (ema * (Decimal(1) - alpha))

    changes = [closes[index] - closes[index - 1] for index in range(1, len(closes))]
    recent_changes = changes[-14:]
    average_gain = sum((max(change, Decimal(0)) for change in recent_changes), Decimal(0)) / Decimal(14)
    average_loss = sum((max(-change, Decimal(0)) for change in recent_changes), Decimal(0)) / Decimal(14)
    if average_loss == 0:
        rsi = Decimal(100) if average_gain > 0 else Decimal(50)
    else:
        rsi = Decimal(100) - (Decimal(100) / (Decimal(1) + (average_gain / average_loss)))

    true_ranges = []
    for index in range(len(bars) - 14, len(bars)):
        bar = bars[index]
        previous_close = bars[index - 1].close
        true_ranges.append(max(bar.high - bar.low, abs(bar.high - previous_close), abs(bar.low - previous_close)))
    atr = sum(true_ranges, Decimal(0)) / Decimal(14)

    average_volume = Decimal(sum(bar.volume for bar in bars[-21:-1])) / Decimal(20)
    volume_ratio = Decimal(bars[-1].volume) / average_volume if average_volume > 0 else Decimal(0)
    quant = Decimal("0.01")
    return TechnicalIndicators(ema.quantize(quant), rsi.quantize(quant), atr.quantize(quant), volume_ratio.quantize(quant))
