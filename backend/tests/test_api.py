import unittest
from unittest import mock

from fastapi.testclient import TestClient

from goblin_guard.api import FixtureProposalProvider, _packet, app


class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.client = TestClient(app)

    def test_health_disables_orders(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.json(),{"status":"ok","order_submission":"disabled"})

    def test_approved_synthetic_evaluation_executes_real_workflow(self):
        payload = self.client.post("/api/evaluations/synthetic",json={"scenario":"approved"}).json()
        self.assertEqual(payload["decision"],"APPROVED")
        self.assertEqual(payload["approvedNotional"],"5,000")
        self.assertEqual(payload["source"],"api_synthetic_workflow")
        self.assertEqual(payload["orderSubmission"],"disabled")
        self.assertEqual([row["event"] for row in payload["trace"]],["Evidence Built","Proposal Validated","Governor Verdict"])

    def test_rejected_synthetic_evaluation_fails_closed(self):
        payload = self.client.post("/api/evaluations/synthetic",json={"scenario":"rejected"}).json()
        self.assertEqual(payload["decision"],"REJECTED")
        self.assertEqual(payload["approvedNotional"],"0")
        self.assertTrue(any(row["status"] == "fail" for row in payload["guardrails"]))

    def test_unknown_scenario_does_not_evaluate(self):
        payload = self.client.post("/api/evaluations/synthetic",json={"scenario":"live"}).json()
        self.assertIn("error",payload)
        self.assertEqual(payload["order_submission"],"disabled")

    def test_no_order_route_exists(self):
        response = self.client.post("/api/orders",json={"symbol":"AAPL"})
        self.assertEqual(response.status_code,404)

    def test_live_endpoint_requires_server_side_credentials(self):
        with mock.patch.dict("os.environ",{},clear=True):
            response = self.client.post("/api/evaluations/live",json={"symbol":"AAPL"})
        self.assertEqual(response.status_code,503)
        self.assertEqual(response.json()["detail"]["order_submission"],"disabled")

    def test_live_endpoint_rejects_symbols_outside_demo_universe(self):
        response = self.client.post("/api/evaluations/live",json={"symbol":"TSLA"})
        self.assertEqual(response.status_code,422)
        self.assertEqual(response.json()["detail"]["order_submission"],"disabled")

    def test_live_endpoint_returns_only_orderless_presentation(self):
        evidence = _packet("approved")
        proposal = FixtureProposalProvider("approved").propose(evidence)
        with mock.patch.dict("os.environ",{"ALPACA_API_KEY":"key","ALPACA_API_SECRET":"secret","OPENAI_API_KEY":"openai"},clear=True), mock.patch("goblin_guard.api.AlpacaMarketDataClient.fetch_recent_bars",return_value=evidence), mock.patch("goblin_guard.api.OpenAIProposalProvider.propose",return_value=proposal):
            response = self.client.post("/api/evaluations/live",json={"symbol":"AAPL"})
        payload = response.json()
        self.assertEqual(response.status_code,200)
        self.assertEqual(payload["source"],"live_read_only_workflow")
        self.assertEqual(payload["orderSubmission"],"disabled")
        self.assertEqual(payload["decision"],"REJECTED")


if __name__ == "__main__": unittest.main()
