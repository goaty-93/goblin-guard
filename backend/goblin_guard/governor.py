from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

from .proposal import Proposal


@dataclass(frozen=True)
class RiskPolicy:
    allowed_symbols: frozenset[str]
    max_trade_notional: Decimal
    daily_loss_limit_pct: Decimal
    max_evidence_age: timedelta
    simulation_only: bool = True
    allowed_actions: frozenset[str] = frozenset({"buy", "hold"})


@dataclass(frozen=True)
class GuardrailResult:
    name: str
    passed: bool
    detail: str


@dataclass(frozen=True)
class Decision:
    status: str
    approved_notional: Decimal
    guardrails: tuple[GuardrailResult, ...]

    @property
    def rejected(self) -> bool:
        return self.status == "rejected"


def evaluate_proposal(*, proposal: Proposal, policy: RiskPolicy, now: datetime, daily_return_pct: Decimal, kill_switch_locked: bool, broker_paper_verified: bool, market_open: bool = True) -> Decision:
    checks: list[GuardrailResult] = []
    checks.append(GuardrailResult("paper_mode", policy.simulation_only and broker_paper_verified, "Paper-only policy and broker endpoint must both be verified."))
    checks.append(GuardrailResult("kill_switch", kill_switch_locked, "Global kill switch must be safe-locked."))
    checks.append(GuardrailResult("market_session", market_open, "Alpaca market clock must report the US equities market open."))
    checks.append(GuardrailResult("symbol_universe", proposal.symbol in policy.allowed_symbols, f"{proposal.symbol} must be in the allowed universe."))
    checks.append(GuardrailResult("action_policy", proposal.action in policy.allowed_actions, f"{proposal.action} must be allowed by the long-only action policy."))
    evidence_age = now - proposal.evidence_as_of
    checks.append(GuardrailResult("evidence_freshness", timedelta(0) <= evidence_age <= policy.max_evidence_age, f"Evidence age {evidence_age}; maximum {policy.max_evidence_age}."))
    checks.append(GuardrailResult("daily_loss", daily_return_pct > policy.daily_loss_limit_pct, f"Daily return {daily_return_pct}% must be above {policy.daily_loss_limit_pct}%."))
    if any(not check.passed for check in checks):
        return Decision("rejected", Decimal("0"), tuple(checks))
    approved = min(proposal.requested_notional, policy.max_trade_notional)
    checks.append(GuardrailResult("per_trade_limit", True, f"Approved {approved} from requested {proposal.requested_notional}."))
    status = "resized" if approved < proposal.requested_notional else "approved"
    return Decision(status, approved, tuple(checks))
