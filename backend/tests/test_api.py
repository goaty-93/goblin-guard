import unittest

from fastapi.testclient import TestClient

from goblin_guard.api import app


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


if __name__ == "__main__": unittest.main()
