from datetime import datetime, timedelta, timezone
from decimal import Decimal
from io import BytesIO
import json
from pathlib import Path
import unittest
from urllib.error import HTTPError, URLError

from goblin_guard.alpaca_paper_orders import AlpacaPaperOrderAdapter, AlpacaPaperOrderConfig, OrderOutcomeUnknown, PaperOrderError
from goblin_guard.api import FixtureProposalProvider, _packet
from goblin_guard.audit import JsonlAuditLog
from goblin_guard.governor import RiskPolicy
from goblin_guard.workflow import EvaluationContext, evaluate_evidence


class Response(BytesIO):
    def __init__(self, payload, request_id="req-test"):
        super().__init__(json.dumps(payload).encode())
        self.headers = {"X-Request-ID": request_id}
    def __enter__(self): return self
    def __exit__(self, *args): self.close()


def approved_result(tmp_path):
    evidence = _packet("approved")
    return evaluate_evidence(
        evidence=evidence,
        provider=FixtureProposalProvider("approved"),
        policy=RiskPolicy(frozenset({"AAPL"}), Decimal("250"), Decimal("-1.5"), timedelta(minutes=60)),
        context=EvaluationContext(datetime(2026,8,28,15,0,tzinfo=timezone.utc),Decimal("0"),True,True,True),
        audit_log=JsonlAuditLog(tmp_path),
    )


class PaperOrderAdapterTests(unittest.TestCase):
    def setUp(self):
        self.result = approved_result(f"/tmp/gg-order-test-{id(self)}.jsonl")

    def test_disabled_by_default(self):
        adapter = AlpacaPaperOrderAdapter(AlpacaPaperOrderConfig("key","secret"))
        with self.assertRaisesRegex(PaperOrderError,"disabled"):
            adapter.submit_approved(self.result)

    def test_host_is_pinned_to_paper(self):
        with self.assertRaises(ValueError):
            AlpacaPaperOrderConfig("key","secret",True,"https://api.alpaca.markets")

    def test_preflights_reconciles_then_submits_bounded_notional(self):
        requests = []
        def opener(request, timeout):
            requests.append(request)
            if request.full_url.endswith("/v2/account"):
                return Response({"status":"ACTIVE","trading_blocked":False})
            if "/v2/assets/AAPL" in request.full_url:
                return Response({"symbol":"AAPL","status":"active","tradable":True,"fractionable":True})
            if "orders:by_client_order_id" in request.full_url:
                raise HTTPError(request.full_url,404,"missing",{},None)
            payload = json.loads(request.data)
            self.assertEqual(payload["notional"],"250")
            self.assertEqual(payload["type"],"market")
            self.assertEqual(payload["time_in_force"],"day")
            self.assertFalse(payload["extended_hours"])
            return Response({"id":"order-1","client_order_id":payload["client_order_id"],"symbol":"AAPL","side":"buy","notional":"250","status":"accepted"})
        receipt = AlpacaPaperOrderAdapter(AlpacaPaperOrderConfig("key","secret",True),opener).submit_approved(self.result)
        self.assertEqual(receipt.order_id,"order-1")
        self.assertFalse(receipt.reconciled)
        self.assertEqual([request.method for request in requests],["GET","GET","GET","POST"])

    def test_existing_client_order_id_prevents_duplicate_post(self):
        methods = []
        def opener(request, timeout):
            methods.append(request.method)
            if request.full_url.endswith("/v2/account"):
                return Response({"status":"ACTIVE","trading_blocked":False})
            if "/v2/assets/AAPL" in request.full_url:
                return Response({"symbol":"AAPL","status":"active","tradable":True,"fractionable":True})
            client_id = request.full_url.split("client_order_id=")[1]
            return Response({"id":"existing","client_order_id":client_id,"symbol":"AAPL","side":"buy","notional":"250","status":"new"})
        receipt = AlpacaPaperOrderAdapter(AlpacaPaperOrderConfig("key","secret",True),opener).submit_approved(self.result)
        self.assertTrue(receipt.reconciled)
        self.assertNotIn("POST",methods)

    def test_submission_appends_correlated_audit_event(self):
        audit_path = f"/tmp/gg-order-audit-{id(self)}.jsonl"
        def opener(request, timeout):
            if request.full_url.endswith("/v2/account"):
                return Response({"status":"ACTIVE","trading_blocked":False})
            if "/v2/assets/AAPL" in request.full_url:
                return Response({"symbol":"AAPL","status":"active","tradable":True,"fractionable":True})
            if "orders:by_client_order_id" in request.full_url:
                raise HTTPError(request.full_url,404,"missing",{},None)
            client_id = json.loads(request.data)["client_order_id"]
            return Response({"id":"order-audit","client_order_id":client_id,"symbol":"AAPL","side":"buy","notional":"250","status":"accepted"})
        adapter = AlpacaPaperOrderAdapter(AlpacaPaperOrderConfig("key","secret",True),opener,JsonlAuditLog(audit_path))
        adapter.submit_approved(self.result)
        event = json.loads(Path(audit_path).read_text(encoding="utf-8").strip())
        self.assertEqual(event["correlation_id"],self.result.correlation_id)
        self.assertEqual(event["event_type"],"paper_order_submitted")
        self.assertEqual(event["details"]["client_order_id"],f"{self.result.correlation_id}-v1")

    def test_ambiguous_submission_reconciles_once(self):
        reconciliation_calls = 0
        def opener(request, timeout):
            nonlocal reconciliation_calls
            if request.full_url.endswith("/v2/account"):
                return Response({"status":"ACTIVE","trading_blocked":False})
            if "/v2/assets/AAPL" in request.full_url:
                return Response({"symbol":"AAPL","status":"active","tradable":True,"fractionable":True})
            if "orders:by_client_order_id" in request.full_url:
                reconciliation_calls += 1
                if reconciliation_calls == 1:
                    raise HTTPError(request.full_url,404,"missing",{},None)
                client_id = request.full_url.split("client_order_id=")[1]
                return Response({"id":"recovered","client_order_id":client_id,"symbol":"AAPL","side":"buy","notional":"250","status":"new"})
            raise URLError("timeout")
        receipt = AlpacaPaperOrderAdapter(AlpacaPaperOrderConfig("key","secret",True),opener).submit_approved(self.result)
        self.assertTrue(receipt.reconciled)
        self.assertEqual(receipt.order_id,"recovered")

    def test_unknown_outcome_never_retries_post(self):
        posts = 0
        reconciliations = 0
        def opener(request, timeout):
            nonlocal posts,reconciliations
            if request.full_url.endswith("/v2/account"):
                return Response({"status":"ACTIVE","trading_blocked":False})
            if "/v2/assets/AAPL" in request.full_url:
                return Response({"symbol":"AAPL","status":"active","tradable":True,"fractionable":True})
            if "orders:by_client_order_id" in request.full_url:
                reconciliations += 1
                raise HTTPError(request.full_url,404,"missing",{},None)
            posts += 1
            raise URLError("timeout")
        with self.assertRaises(OrderOutcomeUnknown):
            AlpacaPaperOrderAdapter(AlpacaPaperOrderConfig("key","secret",True),opener).submit_approved(self.result)
        self.assertEqual(posts,1)
        self.assertEqual(reconciliations,2)

    def test_blocked_account_fails_before_asset_or_order(self):
        calls = []
        def opener(request, timeout):
            calls.append(request.full_url)
            return Response({"status":"ACTIVE","trading_blocked":True})
        with self.assertRaisesRegex(PaperOrderError,"blocked"):
            AlpacaPaperOrderAdapter(AlpacaPaperOrderConfig("key","secret",True),opener).submit_approved(self.result)
        self.assertEqual(len(calls),1)


if __name__ == "__main__": unittest.main()
