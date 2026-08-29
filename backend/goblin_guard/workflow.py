from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
from typing import Protocol

from .audit import AuditEvent, JsonlAuditLog
from .evidence import EvidencePacket
from .governor import Decision, RiskPolicy, evaluate_proposal
from .proposal import Proposal


class ProposalProvider(Protocol):
    def propose(self, evidence: EvidencePacket) -> Proposal: ...


@dataclass(frozen=True)
class EvaluationContext:
    now: datetime
    daily_return_pct: Decimal
    kill_switch_locked: bool
    paper_mode_verified: bool
    market_open: bool = True


@dataclass(frozen=True)
class WorkflowResult:
    correlation_id: str
    evidence: EvidencePacket
    proposal: Proposal
    decision: Decision
    order_submission: str = "disabled"


def correlation_id_for(evidence: EvidencePacket) -> str:
    digest = hashlib.sha256(f"{evidence.evidence_id}:goblin_guard_workflow_v1".encode()).hexdigest()[:20]
    return f"gg-{digest}"


def evaluate_evidence(*, evidence: EvidencePacket, provider: ProposalProvider, policy: RiskPolicy, context: EvaluationContext, audit_log: JsonlAuditLog) -> WorkflowResult:
    correlation_id = correlation_id_for(evidence)
    audit_log.append(AuditEvent(correlation_id, "evidence_built", context.now, {"evidence_id":evidence.evidence_id,"symbol":evidence.symbol,"feed":evidence.feed,"as_of":evidence.as_of,"analysis_context":evidence.analysis_context}))
    proposal = provider.propose(evidence)
    audit_log.append(AuditEvent(correlation_id, "proposal_validated", datetime.now(timezone.utc), {"symbol":proposal.symbol,"action":proposal.action,"requested_notional":proposal.requested_notional,"evidence_refs":list(proposal.evidence_refs)}))
    decision = evaluate_proposal(proposal=proposal, policy=policy, now=context.now, daily_return_pct=context.daily_return_pct, kill_switch_locked=context.kill_switch_locked, broker_paper_verified=context.paper_mode_verified, market_open=context.market_open)
    audit_log.append(AuditEvent(correlation_id, "governor_verdict", datetime.now(timezone.utc), {"status":decision.status,"approved_notional":decision.approved_notional,"checks":[{"name":check.name,"passed":check.passed,"detail":check.detail} for check in decision.guardrails],"order_submission":"disabled"}))
    return WorkflowResult(correlation_id, evidence, proposal, decision)
