from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable

from .paper_order_cli import DEMO_UNIVERSE, submission_eligible
from .workflow import WorkflowResult


@dataclass(frozen=True)
class ScanOutcome:
    symbol: str
    result: WorkflowResult | None = None
    error: str | None = None

    def __post_init__(self) -> None:
        if (self.result is None) == (self.error is None):
            raise ValueError("scan outcome requires exactly one of result or error")
        if self.result is not None and self.result.proposal.symbol != self.symbol:
            raise ValueError("scan result symbol mismatch")

    @property
    def eligible(self) -> bool:
        return self.result is not None and self.result.proposal.action == "buy" and submission_eligible(self.result)

    def document(self) -> dict[str, str | bool | None]:
        if self.result is None:
            return {"symbol":self.symbol,"action":None,"confidence":None,"governor_status":"error","approved_notional":"0","eligible":False,"reason":self.error,"correlation_id":None}
        failed = [check.name for check in self.result.decision.guardrails if not check.passed]
        return {
            "symbol":self.symbol,
            "action":self.result.proposal.action,
            "confidence":str(self.result.proposal.confidence),
            "governor_status":self.result.decision.status,
            "approved_notional":str(self.result.decision.approved_notional),
            "eligible":self.eligible,
            "reason":", ".join(failed) if failed else self.result.proposal.rationale_summary,
            "correlation_id":self.result.correlation_id,
        }


def scan_once(prepare: Callable[[str], WorkflowResult], *, symbols: Iterable[str] = DEMO_UNIVERSE, handled_errors: tuple[type[Exception], ...] = ()) -> tuple[ScanOutcome, ...]:
    requested = tuple(symbols)
    if len(requested) != len(set(requested)):
        raise ValueError("scan universe must not contain duplicate symbols")
    outcomes: list[ScanOutcome] = []
    for symbol in requested:
        try:
            outcomes.append(ScanOutcome(symbol=symbol,result=prepare(symbol)))
        except handled_errors as exc:
            outcomes.append(ScanOutcome(symbol=symbol,error=str(exc)))
    return tuple(outcomes)


def select_candidate(outcomes: Iterable[ScanOutcome]) -> ScanOutcome | None:
    eligible = [outcome for outcome in outcomes if outcome.eligible]
    if not eligible:
        return None
    return min(eligible,key=lambda outcome: (-outcome.result.proposal.confidence,outcome.symbol))  # type: ignore[union-attr]
