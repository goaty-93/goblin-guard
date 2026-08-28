from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .evidence import EvidencePacket
from .proposal import Proposal, ProposalValidationError


class ProposalProviderUnavailable(RuntimeError):
    """Safe public error for model transport, refusal, or invalid output."""


PROPOSAL_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["schema_version", "symbol", "action", "requested_notional", "confidence", "evidence_refs", "evidence_as_of", "rationale_summary"],
    "properties": {
        "schema_version": {"type":"string", "const":"goblin_guard_proposal_v1"},
        "symbol": {"type":"string", "pattern":"^[A-Z][A-Z0-9.]{0,9}$"},
        "action": {"type":"string", "enum":["buy","sell","hold"]},
        "requested_notional": {"type":"number", "exclusiveMinimum":0},
        "confidence": {"type":"number", "minimum":0, "maximum":1},
        "evidence_refs": {"type":"array", "minItems":1, "items":{"type":"string"}},
        "evidence_as_of": {"type":"string"},
        "rationale_summary": {"type":"string", "minLength":12, "maxLength":500},
    },
}


@dataclass(frozen=True)
class OpenAIProposalConfig:
    api_key: str
    model: str = "gpt-5.6-luna"
    base_url: str = "https://api.openai.com/v1"
    timeout_seconds: float = 20.0

    def __post_init__(self) -> None:
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        if self.base_url.rstrip("/") != "https://api.openai.com/v1":
            raise ValueError("OpenAI base URL must be https://api.openai.com/v1")


class OpenAIProposalProvider:
    def __init__(self, config: OpenAIProposalConfig, opener: Callable[..., Any] = urlopen):
        self.config = config
        self._opener = opener

    def propose(self, evidence: EvidencePacket) -> Proposal:
        request_body = {
            "model": self.config.model,
            "store": False,
            "max_output_tokens": 600,
            "reasoning": {"effort":"low"},
            "instructions": (
                "You are Goblin Guard's proposal analyst. Use only the supplied evidence packet. "
                "Return one bounded proposal. Cite only its evidence_id. Never claim to execute, approve, "
                "or bypass risk controls. If evidence is insufficient, choose hold."
            ),
            "input": json.dumps(evidence.proposal_view(), sort_keys=True, separators=(",", ":")),
            "tools": [],
            "tool_choice": "none",
            "text": {"format":{"type":"json_schema","name":"goblin_guard_proposal","strict":True,"schema":PROPOSAL_SCHEMA}},
        }
        request = Request(
            f"{self.config.base_url.rstrip('/')}/responses",
            data=json.dumps(request_body).encode("utf-8"),
            method="POST",
            headers={"Authorization":f"Bearer {self.config.api_key}","Content-Type":"application/json","Accept":"application/json"},
        )
        try:
            with self._opener(request, timeout=self.config.timeout_seconds) as response:
                payload = json.load(response)
        except HTTPError as exc:
            raise ProposalProviderUnavailable(f"OpenAI proposal service returned HTTP {exc.code}") from None
        except (URLError, TimeoutError, json.JSONDecodeError):
            raise ProposalProviderUnavailable("OpenAI proposal service is unavailable") from None
        if not isinstance(payload, dict) or payload.get("status") != "completed":
            raise ProposalProviderUnavailable("OpenAI proposal did not complete")
        output_text = payload.get("output_text")
        if not isinstance(output_text, str):
            raise ProposalProviderUnavailable("OpenAI proposal contained no structured output")
        try:
            candidate = json.loads(output_text)
            return Proposal.from_untrusted(candidate, {evidence.evidence_id})
        except (json.JSONDecodeError, ProposalValidationError) as exc:
            raise ProposalProviderUnavailable(f"OpenAI proposal failed local validation: {exc}") from None
