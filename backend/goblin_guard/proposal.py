from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
import re
from typing import Any, Collection


class ProposalValidationError(ValueError):
    """Raised when untrusted model output violates the proposal contract."""


@dataclass(frozen=True)
class Proposal:
    schema_version: str
    symbol: str
    action: str
    requested_notional: Decimal
    confidence: Decimal
    evidence_refs: tuple[str, ...]
    evidence_as_of: datetime
    rationale_summary: str

    @classmethod
    def from_untrusted(cls, payload: Any, known_evidence_refs: Collection[str]) -> "Proposal":
        if not isinstance(payload, dict):
            raise ProposalValidationError("proposal must be an object")
        expected = {"schema_version", "symbol", "action", "requested_notional", "confidence", "evidence_refs", "evidence_as_of", "rationale_summary"}
        if set(payload) != expected:
            missing, extra = expected - set(payload), set(payload) - expected
            raise ProposalValidationError(f"proposal fields mismatch; missing={sorted(missing)}, extra={sorted(extra)}")
        if payload["schema_version"] != "goblin_guard_proposal_v1":
            raise ProposalValidationError("unsupported schema_version")
        symbol = payload["symbol"]
        if not isinstance(symbol, str) or not re.fullmatch(r"[A-Z][A-Z0-9.]{0,9}", symbol):
            raise ProposalValidationError("invalid symbol")
        action = payload["action"]
        if action not in {"buy", "sell", "hold"}:
            raise ProposalValidationError("action must be buy, sell, or hold")
        try:
            notional = Decimal(str(payload["requested_notional"]))
            confidence = Decimal(str(payload["confidence"]))
        except (InvalidOperation, ValueError):
            raise ProposalValidationError("notional and confidence must be numeric") from None
        if not notional.is_finite() or notional <= 0:
            raise ProposalValidationError("requested_notional must be finite and positive")
        if not confidence.is_finite() or not Decimal("0") <= confidence <= Decimal("1"):
            raise ProposalValidationError("confidence must be between 0 and 1")
        refs = payload["evidence_refs"]
        if not isinstance(refs, list) or not refs or any(not isinstance(ref, str) for ref in refs):
            raise ProposalValidationError("evidence_refs must be a non-empty string list")
        unknown = set(refs) - set(known_evidence_refs)
        if unknown:
            raise ProposalValidationError(f"unknown evidence refs: {sorted(unknown)}")
        try:
            evidence_as_of = datetime.fromisoformat(payload["evidence_as_of"].replace("Z", "+00:00"))
        except (AttributeError, ValueError):
            raise ProposalValidationError("evidence_as_of must be ISO-8601") from None
        if evidence_as_of.tzinfo is None:
            raise ProposalValidationError("evidence_as_of must include a timezone")
        summary = payload["rationale_summary"]
        if not isinstance(summary, str) or not 12 <= len(summary) <= 500:
            raise ProposalValidationError("rationale_summary must contain 12-500 characters")
        return cls("goblin_guard_proposal_v1", symbol, action, notional, confidence, tuple(refs), evidence_as_of, summary)
