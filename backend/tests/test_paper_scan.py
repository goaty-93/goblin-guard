from datetime import datetime, timedelta, timezone
from decimal import Decimal
import unittest

from goblin_guard.audit import JsonlAuditLog
from goblin_guard.evidence import build_evidence_packet
from goblin_guard.governor import RiskPolicy
from goblin_guard.paper_order_cli import DEMO_UNIVERSE
from goblin_guard.paper_scan import ScanOutcome, scan_once, select_candidate
from goblin_guard.proposal import Proposal
from goblin_guard.workflow import EvaluationContext, evaluate_evidence


NOW = datetime(2026,8,28,12,0,tzinfo=timezone.utc)


def result(symbol: str, *, action: str = "buy", confidence: str = "0.7"):
    bars = [{"t":f"2026-08-28T11:{minute:02d}:00Z","o":100,"h":101,"l":99,"c":100,"v":1000,"n":10,"vw":100} for minute in range(21,42)]
    evidence = build_evidence_packet(symbol=symbol,feed="iex",fetched_at=NOW,raw_bars=bars)
    class Provider:
        def propose(self, packet):
            return Proposal.from_untrusted({"schema_version":"goblin_guard_proposal_v1","symbol":symbol,"action":action,"requested_notional":"1" if action != "hold" else "0","confidence":confidence,"evidence_refs":[packet.evidence_id],"evidence_as_of":packet.as_of.isoformat(),"rationale_summary":"Deterministic scanner test proposal with sufficient supporting text."},{packet.evidence_id})
    return evaluate_evidence(evidence=evidence,provider=Provider(),policy=RiskPolicy(frozenset(DEMO_UNIVERSE),Decimal("1"),Decimal("-1.5"),timedelta(minutes=60)),context=EvaluationContext(NOW,Decimal("0"),True,True,True),audit_log=JsonlAuditLog(f"/tmp/gg-scan-{symbol}-{action}-{confidence}.jsonl"))


class PaperScanTests(unittest.TestCase):
    def test_fixed_universe_is_exact_and_stable(self):
        self.assertEqual(DEMO_UNIVERSE,("AAPL","MSFT","AMZN","GOOGL","META","NVDA"))

    def test_scan_calls_each_symbol_once_and_keeps_errors(self):
        calls = []
        def prepare(symbol):
            calls.append(symbol)
            if symbol == "MSFT":
                raise RuntimeError("evidence unavailable")
            return result(symbol,action="hold")
        outcomes = scan_once(prepare,symbols=("AAPL","MSFT"),handled_errors=(RuntimeError,))
        self.assertEqual(calls,["AAPL","MSFT"])
        self.assertEqual(len(outcomes),2)
        self.assertEqual(outcomes[1].document()["governor_status"],"error")

    def test_highest_confidence_eligible_buy_wins(self):
        outcomes = (ScanOutcome("AAPL",result=result("AAPL",confidence="0.71")),ScanOutcome("MSFT",result=result("MSFT",confidence="0.82")),ScanOutcome("AMZN",result=result("AMZN",action="hold",confidence="0.99")))
        self.assertEqual(select_candidate(outcomes).symbol,"MSFT")

    def test_symbol_breaks_confidence_tie(self):
        outcomes = (ScanOutcome("MSFT",result=result("MSFT",confidence="0.8")),ScanOutcome("AAPL",result=result("AAPL",confidence="0.8")))
        self.assertEqual(select_candidate(outcomes).symbol,"AAPL")

    def test_no_candidate_when_all_hold_or_sell(self):
        outcomes = (ScanOutcome("AAPL",result=result("AAPL",action="hold")),ScanOutcome("MSFT",result=result("MSFT",action="sell")))
        self.assertIsNone(select_candidate(outcomes))


if __name__ == "__main__":
    unittest.main()
