from datetime import datetime, timezone
import io
import json
import unittest
from urllib.error import HTTPError

from goblin_guard import OpenAIProposalConfig, OpenAIProposalProvider, ProposalProviderUnavailable, build_evidence_packet


NOW = datetime(2026, 8, 28, 15, 0, tzinfo=timezone.utc)
BAR = {"t":"2026-08-28T14:59:00Z","o":190.5,"h":192.0,"l":190.2,"c":191.8,"v":1700,"n":61,"vw":191.4}


class Response(io.BytesIO):
    def __enter__(self): return self
    def __exit__(self, *args): self.close()


class OpenAIProviderTests(unittest.TestCase):
    def setUp(self):
        self.evidence = build_evidence_packet(symbol="AAPL", feed="synthetic", fetched_at=NOW, raw_bars=[BAR], source="test")

    def candidate(self, **overrides):
        value = {"schema_version":"goblin_guard_proposal_v1","symbol":"AAPL","action":"buy","requested_notional":250,"confidence":0.72,"evidence_refs":[self.evidence.evidence_id],"evidence_as_of":"2026-08-28T14:59:00Z","rationale_summary":"Supplied bar evidence supports a bounded paper proposal."}
        value.update(overrides)
        return value

    def test_request_has_no_tools_and_response_is_locally_validated(self):
        seen = {}
        def opener(request, timeout):
            seen.update(body=json.loads(request.data), headers=dict(request.header_items()), url=request.full_url)
            return Response(json.dumps({"status":"completed","output_text":json.dumps(self.candidate())}).encode())
        proposal = OpenAIProposalProvider(OpenAIProposalConfig("test-openai-key"), opener).propose(self.evidence)
        self.assertEqual(proposal.symbol, "AAPL")
        self.assertEqual(seen["body"]["tools"], [])
        self.assertEqual(seen["body"]["tool_choice"], "none")
        self.assertFalse(seen["body"]["store"])
        self.assertTrue(seen["body"]["text"]["format"]["strict"])
        self.assertNotIn("test-openai-key", json.dumps(seen["body"]))

    def test_unknown_evidence_reference_fails_closed(self):
        def opener(request, timeout):
            return Response(json.dumps({"status":"completed","output_text":json.dumps(self.candidate(evidence_refs=["invented"]))}).encode())
        with self.assertRaises(ProposalProviderUnavailable):
            OpenAIProposalProvider(OpenAIProposalConfig("key"), opener).propose(self.evidence)

    def test_incomplete_response_fails_closed(self):
        def opener(request, timeout):
            return Response(json.dumps({"status":"incomplete","output_text":""}).encode())
        with self.assertRaisesRegex(ProposalProviderUnavailable, "did not complete"):
            OpenAIProposalProvider(OpenAIProposalConfig("key"), opener).propose(self.evidence)

    def test_http_error_is_redacted(self):
        def opener(request, timeout):
            raise HTTPError(request.full_url, 429, "secret detail", {}, None)
        with self.assertRaisesRegex(ProposalProviderUnavailable, "HTTP 429") as caught:
            OpenAIProposalProvider(OpenAIProposalConfig("test-openai-key"), opener).propose(self.evidence)
        self.assertNotIn("test-openai-key", str(caught.exception))


if __name__ == "__main__": unittest.main()
