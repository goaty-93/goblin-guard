from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import json
from pathlib import Path
import tempfile

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .audit import JsonlAuditLog
from .evidence import EvidencePacket, build_evidence_packet
from .governor import RiskPolicy
from .proposal import Proposal
from .workflow import EvaluationContext, evaluate_evidence


DEMO_NOW = datetime(2026, 8, 28, 15, 0, tzinfo=timezone.utc)


class EvaluationRequest(BaseModel):
    scenario: str = "approved"


class FixtureProposalProvider:
    def __init__(self, scenario: str): self.scenario = scenario
    def propose(self, evidence: EvidencePacket) -> Proposal:
        rejected = self.scenario == "rejected"
        return Proposal.from_untrusted({
            "schema_version":"goblin_guard_proposal_v1", "symbol":evidence.symbol,
            "action":"buy", "requested_notional":19250 if rejected else 8000,
            "confidence":0.72 if rejected else 0.81, "evidence_refs":[evidence.evidence_id],
            "evidence_as_of":evidence.as_of.isoformat(),
            "rationale_summary":"Momentum evidence supports a bounded proposal that remains subject to independent deterministic controls.",
        }, {evidence.evidence_id})


def _packet(scenario: str) -> EvidencePacket:
    fixture_path = Path(__file__).resolve().parents[1] / "fixtures" / "alpaca-bars-aapl.json"
    payload = json.loads(fixture_path.read_text(encoding="utf-8"))
    bars = payload["bars"]
    if scenario == "approved":
        shifted = []
        for index, bar in enumerate(bars):
            item = dict(bar)
            item["t"] = (DEMO_NOW - timedelta(minutes=len(bars)-index)).isoformat().replace("+00:00","Z")
            shifted.append(item)
        bars = shifted
    return build_evidence_packet(symbol="AAPL",feed="synthetic",fetched_at=DEMO_NOW,raw_bars=bars,source="synthetic_api_fixture")


def _present(scenario: str) -> dict:
    evidence = _packet(scenario)
    rejected = scenario == "rejected"
    context = EvaluationContext(
        DEMO_NOW if not rejected else DEMO_NOW + timedelta(hours=3),
        Decimal("-1.72") if rejected else Decimal("-0.32"), True, True,
    )
    policy = RiskPolicy(frozenset({"AAPL"}),Decimal("5000"),Decimal("-1.5"),timedelta(minutes=60))
    with tempfile.TemporaryDirectory(prefix="goblin-guard-api-") as directory:
        audit_path = Path(directory)/"audit.jsonl"
        result = evaluate_evidence(evidence=evidence,provider=FixtureProposalProvider(scenario),policy=policy,context=context,audit_log=JsonlAuditLog(audit_path))
        audit = [json.loads(line) for line in audit_path.read_text().splitlines()]
    bars = evidence.bars
    checks = []
    for check in result.decision.guardrails:
        status = "pass" if check.passed else ("warn" if check.name == "evidence_freshness" else "fail")
        checks.append({"label":check.name.replace("_"," ").title(),"detail":check.detail,"status":status})
    decision = "REJECTED" if result.decision.rejected else "APPROVED"
    trace = []
    for index, event in enumerate(audit):
        status = "fail" if event["event_type"] == "governor_verdict" and result.decision.rejected else "pass"
        trace.append({"time":f"15:00:0{index}","event":event["event_type"].replace("_"," ").title(),"status":status,"result":decision if event["event_type"] == "governor_verdict" else "PASS","detail":result.correlation_id})
    latest = bars[-1]
    return {
        "id":result.correlation_id.upper(),"symbol":"AAPL","company":"Apple Inc.","action":result.proposal.action.upper(),
        "requestedNotional":f"{result.proposal.requested_notional:,.0f}","approvedNotional":f"{result.decision.approved_notional:,.0f}","limitPrice":str(latest.close),
        "confidence":f"{result.proposal.confidence*100:.0f}%","dataAsOf":evidence.as_of.strftime("%d %b %Y %H:%M UTC"),"stale":rejected,
        "rationale":result.proposal.rationale_summary,"metrics":{"lastPrice":str(latest.close),"ema20":"188.42","rsi":"58.7","volume":"1.32×","atr":str(latest.high-latest.low)},
        "decision":decision,"decisionReason":"Stale evidence; daily loss circuit breaker" if rejected else "Approved with deterministic size reduction",
        "guardrails":checks,"trace":trace,"source":"api_synthetic_workflow","orderSubmission":result.order_submission,
    }


app = FastAPI(title="Goblin Guard API", version="0.2.0", docs_url=None, redoc_url=None)
app.add_middleware(CORSMiddleware,allow_origins=["http://127.0.0.1:4173","http://localhost:4173"],allow_credentials=False,allow_methods=["GET","POST"],allow_headers=["Content-Type"])


@app.get("/api/health")
def health(): return {"status":"ok","order_submission":"disabled"}


@app.post("/api/evaluations/synthetic")
def synthetic_evaluation(request: EvaluationRequest):
    scenario = request.scenario.lower()
    if scenario not in {"approved","rejected"}:
        return {"error":"scenario must be approved or rejected","order_submission":"disabled"}
    return _present(scenario)
