from __future__ import annotations

import argparse
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import json
import os
from pathlib import Path
import sys

from .alpaca_clock import AlpacaClockClient, AlpacaClockConfig, MarketClockUnavailable
from .alpaca_market_data import AlpacaMarketDataClient, AlpacaMarketDataConfig, MarketDataUnavailable
from .alpaca_paper_orders import AlpacaPaperOrderAdapter, AlpacaPaperOrderConfig, PaperOrderError, client_order_id_for
from .api import DEMO_NOW, FixtureProposalProvider, _packet
from .audit import JsonlAuditLog
from .governor import RiskPolicy
from .indicators import IndicatorUnavailable, calculate_indicators
from .openai_provider import OpenAIProposalConfig, OpenAIProposalProvider, ProposalProviderUnavailable
from .workflow import EvaluationContext, WorkflowResult, evaluate_evidence


def _credentials() -> tuple[str, str, str]:
    return os.getenv("ALPACA_API_KEY", ""), os.getenv("ALPACA_API_SECRET", ""), os.getenv("OPENAI_API_KEY", "")


def prepare_result(*, symbol: str, synthetic: bool, audit_log: JsonlAuditLog) -> WorkflowResult:
    policy = RiskPolicy(frozenset({"AAPL", "MSFT"}), Decimal("1.00"), Decimal("-1.5"), timedelta(minutes=60))
    if synthetic:
        evidence = _packet("approved")
        return evaluate_evidence(
            evidence=evidence, provider=FixtureProposalProvider("approved"), policy=policy,
            context=EvaluationContext(DEMO_NOW, Decimal("0"), True, True, True), audit_log=audit_log,
        )

    alpaca_key, alpaca_secret, openai_key = _credentials()
    if not alpaca_key or not alpaca_secret or not openai_key:
        raise PaperOrderError("live preparation requires server-side Alpaca paper and OpenAI credentials")
    now = datetime.now(timezone.utc)
    config = AlpacaPaperOrderConfig(alpaca_key, alpaca_secret)
    adapter = AlpacaPaperOrderAdapter(config)
    account = adapter.account_snapshot()
    clock = AlpacaClockClient(AlpacaClockConfig(alpaca_key, alpaca_secret)).fetch()
    evidence = AlpacaMarketDataClient(AlpacaMarketDataConfig(alpaca_key, alpaca_secret)).fetch_recent_bars(symbol, now=now)
    indicators = calculate_indicators(evidence.bars)
    evidence = replace(evidence, analysis_context={"technical_indicators":indicators.proposal_view(),"market_clock":clock.proposal_view()})
    provider = OpenAIProposalProvider(OpenAIProposalConfig(openai_key))
    return evaluate_evidence(
        evidence=evidence, provider=provider, policy=policy,
        context=EvaluationContext(now, account.daily_return_pct, True, True, clock.is_open), audit_log=audit_log,
    )


def preview(result: WorkflowResult, *, synthetic: bool) -> dict[str, str | bool]:
    return {
        "mode": "synthetic_rehearsal" if synthetic else "live_paper",
        "correlation_id": result.correlation_id,
        "client_order_id": client_order_id_for(result),
        "symbol": result.proposal.symbol,
        "side": result.proposal.action,
        "requested_notional": str(result.proposal.requested_notional),
        "governor_status": result.decision.status,
        "approved_notional": str(result.decision.approved_notional),
        "order_submission": "disabled" if synthetic or result.decision.rejected else "confirmation_required",
    }


def confirmation_matches(expected: str, entered: str) -> bool:
    return entered.strip() == expected


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Prepare or explicitly submit one guarded Alpaca paper order.")
    parser.add_argument("--symbol", choices=("AAPL", "MSFT"), default="AAPL")
    parser.add_argument("--synthetic", action="store_true", help="Run a credential-free rehearsal; submission is impossible.")
    parser.add_argument("--execute", action="store_true", help="Permit one confirmed POST to the pinned Alpaca paper endpoint.")
    parser.add_argument("--audit-path", default="audit/paper-orders.jsonl")
    args = parser.parse_args(argv)
    if args.synthetic and args.execute:
        parser.error("--synthetic cannot be combined with --execute")

    audit_log = JsonlAuditLog(Path(args.audit_path))
    try:
        result = prepare_result(symbol=args.symbol, synthetic=args.synthetic, audit_log=audit_log)
    except (PaperOrderError, MarketClockUnavailable, MarketDataUnavailable, IndicatorUnavailable, ProposalProviderUnavailable) as exc:
        print(json.dumps({"error":str(exc),"order_submission":"disabled"},sort_keys=True), file=sys.stderr)
        return 2

    document = preview(result, synthetic=args.synthetic)
    print(json.dumps(document, indent=2, sort_keys=True))
    if result.decision.rejected:
        print("Governor rejected the proposal; no order can be submitted.", file=sys.stderr)
        return 3
    if args.synthetic or not args.execute:
        print("Preview only. No order submitted.")
        return 0

    expected = client_order_id_for(result)
    print(f"Type the complete client order ID to submit exactly one PAPER order: {expected}", file=sys.stderr)
    if not confirmation_matches(expected, input("> ")):
        print("Confirmation did not match. No order submitted.", file=sys.stderr)
        return 4
    alpaca_key, alpaca_secret, _ = _credentials()
    adapter = AlpacaPaperOrderAdapter(AlpacaPaperOrderConfig(alpaca_key, alpaca_secret, submission_enabled=True), audit_log=audit_log)
    try:
        receipt = adapter.submit_approved(result)
    except PaperOrderError as exc:
        print(json.dumps({"error":str(exc),"order_submission":"not_confirmed"},sort_keys=True), file=sys.stderr)
        return 5
    print(json.dumps({"order_id":receipt.order_id,"client_order_id":receipt.client_order_id,"status":receipt.status,"reconciled":receipt.reconciled,"order_submission":"paper"},indent=2,sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
