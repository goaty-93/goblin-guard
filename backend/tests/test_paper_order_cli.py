from decimal import Decimal
import unittest

from goblin_guard.alpaca_paper_orders import PaperAccountSnapshot
from goblin_guard.paper_order_cli import confirmation_matches, preview
from goblin_guard.api import FixtureProposalProvider, _packet
from goblin_guard.audit import JsonlAuditLog
from goblin_guard.governor import RiskPolicy
from goblin_guard.workflow import EvaluationContext, evaluate_evidence
from goblin_guard.api import DEMO_NOW
from datetime import timedelta


class PaperOrderCliTests(unittest.TestCase):
    def test_confirmation_requires_exact_full_client_order_id(self):
        expected = "gg-123-v1"
        self.assertTrue(confirmation_matches(expected, expected))
        self.assertFalse(confirmation_matches(expected, "yes"))
        self.assertFalse(confirmation_matches(expected, "gg-123"))

    def test_account_daily_return_uses_prior_equity(self):
        snapshot = PaperAccountSnapshot("ACTIVE",False,Decimal("990"),Decimal("1000"),Decimal("500"))
        self.assertEqual(snapshot.daily_return_pct,Decimal("-1.00"))

    def test_synthetic_preview_cannot_claim_submission(self):
        evidence = _packet("approved")
        result = evaluate_evidence(
            evidence=evidence, provider=FixtureProposalProvider("approved"),
            policy=RiskPolicy(frozenset({"AAPL"}),Decimal("1"),Decimal("-1.5"),timedelta(minutes=60)),
            context=EvaluationContext(DEMO_NOW,Decimal("0"),True,True,True),
            audit_log=JsonlAuditLog(f"/tmp/gg-cli-preview-{id(self)}.jsonl"),
        )
        document = preview(result,synthetic=True)
        self.assertEqual(document["order_submission"],"disabled")
        self.assertEqual(document["approved_notional"],"1")

    def test_rejected_live_preview_disables_submission(self):
        evidence = _packet("approved")
        result = evaluate_evidence(
            evidence=evidence, provider=FixtureProposalProvider("approved"),
            policy=RiskPolicy(frozenset({"AAPL"}),Decimal("1"),Decimal("-1.5"),timedelta(minutes=60)),
            context=EvaluationContext(DEMO_NOW,Decimal("-1.5"),True,True,True),
            audit_log=JsonlAuditLog(f"/tmp/gg-cli-rejected-{id(self)}.jsonl"),
        )
        self.assertTrue(result.decision.rejected)
        self.assertEqual(preview(result,synthetic=False)["order_submission"],"disabled")


if __name__ == "__main__": unittest.main()
