from datetime import datetime, timedelta, timezone
from decimal import Decimal
import json
from pathlib import Path
import tempfile
import unittest

from goblin_guard import JsonlAuditLog, Proposal, RiskPolicy, build_evidence_packet
from goblin_guard.workflow import EvaluationContext, correlation_id_for, evaluate_evidence


NOW = datetime(2026,8,28,15,0,tzinfo=timezone.utc)
BAR = {"t":"2026-08-28T14:59:00Z","o":190.5,"h":192.0,"l":190.2,"c":191.8,"v":1700,"n":61,"vw":191.4}


class FixtureProvider:
    def __init__(self, requested_notional="8000"): self.requested_notional = requested_notional
    def propose(self, evidence):
        return Proposal.from_untrusted({"schema_version":"goblin_guard_proposal_v1","symbol":evidence.symbol,"action":"buy","requested_notional":self.requested_notional,"confidence":"0.72","evidence_refs":[evidence.evidence_id],"evidence_as_of":evidence.as_of.isoformat(),"rationale_summary":"Validated fixture proposal grounded in supplied market bars."},{evidence.evidence_id})


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.evidence = build_evidence_packet(symbol="AAPL",feed="synthetic",fetched_at=NOW,raw_bars=[BAR],source="test")
        self.policy = RiskPolicy(frozenset({"AAPL"}),Decimal("5000"),Decimal("-1.5"),timedelta(minutes=60))
        self.context = EvaluationContext(NOW,Decimal("-0.3"),True,True)

    def test_orderless_vertical_slice_resizes_and_appends_trace(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/"audit.jsonl"
            result = evaluate_evidence(evidence=self.evidence,provider=FixtureProvider(),policy=self.policy,context=self.context,audit_log=JsonlAuditLog(path))
            self.assertEqual(result.decision.status,"resized")
            self.assertEqual(result.decision.approved_notional,Decimal("5000"))
            self.assertEqual(result.order_submission,"disabled")
            events = [json.loads(line) for line in path.read_text().splitlines()]
            self.assertEqual([event["event_type"] for event in events],["evidence_built","proposal_validated","governor_verdict"])
            self.assertTrue(all(event["correlation_id"] == result.correlation_id for event in events))
            self.assertEqual(events[-1]["details"]["order_submission"],"disabled")

    def test_correlation_id_is_stable_for_replay(self):
        self.assertEqual(correlation_id_for(self.evidence),correlation_id_for(self.evidence))

    def test_stale_evidence_is_rejected_without_order(self):
        stale = EvaluationContext(NOW+timedelta(hours=2),Decimal("-0.3"),True,True)
        with tempfile.TemporaryDirectory() as directory:
            result = evaluate_evidence(evidence=self.evidence,provider=FixtureProvider("250"),policy=self.policy,context=stale,audit_log=JsonlAuditLog(Path(directory)/"audit.jsonl"))
            self.assertTrue(result.decision.rejected)
            self.assertEqual(result.order_submission,"disabled")


if __name__ == "__main__": unittest.main()
