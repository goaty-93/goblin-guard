from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import argparse
import json
from pathlib import Path
import sys

from .alpaca_clock import AlpacaClockClient, AlpacaClockConfig, MarketClockUnavailable
from .alpaca_market_data import AlpacaMarketDataClient, AlpacaMarketDataConfig, MarketDataUnavailable
from .alpaca_paper_orders import AlpacaPaperOrderAdapter, AlpacaPaperOrderConfig, PaperOrderError
from .audit import JsonlAuditLog
from .governor import RiskPolicy
from .indicators import IndicatorUnavailable, calculate_indicators
from .openai_provider import OpenAIProposalConfig, OpenAIProposalProvider, ProposalProviderUnavailable
from .paper_order_cli import DEMO_UNIVERSE, _credentials, proposal_analysis_context
from .paper_scan import scan_once, select_candidate
from .workflow import EvaluationContext, evaluate_evidence


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Preview one auditable pass over the fixed Goblin Guard universe. No order submission exists here.")
    parser.add_argument("--audit-path",default="audit/paper-scan.jsonl")
    args = parser.parse_args(argv)
    alpaca_key, alpaca_secret, openai_key = _credentials()
    if not alpaca_key or not alpaca_secret or not openai_key:
        print(json.dumps({"error":"scan requires server-side Alpaca paper and OpenAI credentials","order_submission":"disabled"},sort_keys=True),file=sys.stderr)
        return 2
    audit_log = JsonlAuditLog(Path(args.audit_path))
    now = datetime.now(timezone.utc)
    try:
        account = AlpacaPaperOrderAdapter(AlpacaPaperOrderConfig(alpaca_key,alpaca_secret)).account_snapshot()
        clock = AlpacaClockClient(AlpacaClockConfig(alpaca_key,alpaca_secret)).fetch()
        daily_return_pct = account.daily_return_pct
    except (PaperOrderError,MarketClockUnavailable) as exc:
        print(json.dumps({"error":str(exc),"order_submission":"disabled"},sort_keys=True),file=sys.stderr)
        return 2
    market_data = AlpacaMarketDataClient(AlpacaMarketDataConfig(alpaca_key,alpaca_secret))
    provider = OpenAIProposalProvider(OpenAIProposalConfig(openai_key))
    policy = RiskPolicy(frozenset(DEMO_UNIVERSE),Decimal("1.00"),Decimal("-1.5"),timedelta(minutes=60))
    context = EvaluationContext(now,daily_return_pct,True,True,clock.is_open)

    def prepare(symbol: str):
        evidence = market_data.fetch_recent_bars(symbol,now=now)
        indicators = calculate_indicators(evidence.bars)
        enriched = replace(evidence,analysis_context=proposal_analysis_context(indicators=indicators.proposal_view(),market_clock=clock.proposal_view()))
        return evaluate_evidence(evidence=enriched,provider=provider,policy=policy,context=context,audit_log=audit_log)

    outcomes = scan_once(prepare,handled_errors=(MarketDataUnavailable,IndicatorUnavailable,ProposalProviderUnavailable))
    selected = select_candidate(outcomes)
    print(json.dumps({
        "mode":"live_paper_scan_preview","universe":list(DEMO_UNIVERSE),"evaluated_at":now.isoformat(),
        "market_open":clock.is_open,"results":[outcome.document() for outcome in outcomes],
        "selected_symbol":selected.symbol if selected else None,
        "selection_rule":"highest-confidence eligible long-only buy; ticker ascending breaks ties",
        "order_submission":"disabled",
    },indent=2,sort_keys=True))
    print("Scan preview only. No order submitted.")
    return 0 if selected else 3


if __name__ == "__main__":
    raise SystemExit(main())
