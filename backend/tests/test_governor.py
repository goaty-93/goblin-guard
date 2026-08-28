from datetime import datetime, timedelta, timezone
from decimal import Decimal
import unittest

from goblin_guard import Proposal, ProposalValidationError, RiskPolicy, evaluate_proposal


NOW = datetime(2026, 8, 28, 12, 0, tzinfo=timezone.utc)


def payload(**overrides):
    base = {"schema_version":"goblin_guard_proposal_v1","symbol":"AAPL","action":"buy","requested_notional":"8000","confidence":"0.72","evidence_refs":["bars:AAPL:20260828T115500Z"],"evidence_as_of":"2026-08-28T11:55:00Z","rationale_summary":"Fresh momentum evidence supports a measured paper trade."}
    base.update(overrides)
    return base


class GovernorTests(unittest.TestCase):
    def setUp(self):
        self.proposal = Proposal.from_untrusted(payload(), {"bars:AAPL:20260828T115500Z"})
        self.policy = RiskPolicy(frozenset({"AAPL", "MSFT"}), Decimal("5000"), Decimal("-1.5"), timedelta(minutes=60))

    def decide(self, **overrides):
        args = {"proposal":self.proposal,"policy":self.policy,"now":NOW,"daily_return_pct":Decimal("-0.3"),"kill_switch_locked":True,"broker_paper_verified":True}
        args.update(overrides)
        return evaluate_proposal(**args)

    def test_valid_proposal_is_resized_deterministically(self):
        decision = self.decide()
        self.assertEqual(decision.status, "resized")
        self.assertEqual(decision.approved_notional, Decimal("5000"))

    def test_unknown_evidence_reference_is_rejected_at_schema_boundary(self):
        with self.assertRaises(ProposalValidationError):
            Proposal.from_untrusted(payload(evidence_refs=["invented"]), {"bars:AAPL:20260828T115500Z"})

    def test_hold_requires_exactly_zero_notional(self):
        hold = Proposal.from_untrusted(payload(action="hold",requested_notional="0"),{"bars:AAPL:20260828T115500Z"})
        self.assertEqual(hold.requested_notional,Decimal("0"))
        with self.assertRaises(ProposalValidationError):
            Proposal.from_untrusted(payload(action="hold",requested_notional="0.01"),{"bars:AAPL:20260828T115500Z"})

    def test_stale_evidence_fails_closed(self):
        decision = self.decide(now=NOW + timedelta(hours=2))
        self.assertTrue(decision.rejected)
        self.assertEqual(decision.approved_notional, Decimal("0"))

    def test_daily_loss_boundary_fails_closed(self):
        self.assertTrue(self.decide(daily_return_pct=Decimal("-1.5")).rejected)

    def test_unverified_paper_endpoint_fails_closed(self):
        self.assertTrue(self.decide(broker_paper_verified=False).rejected)

    def test_unlocked_kill_switch_fails_closed(self):
        self.assertTrue(self.decide(kill_switch_locked=False).rejected)


if __name__ == "__main__":
    unittest.main()
