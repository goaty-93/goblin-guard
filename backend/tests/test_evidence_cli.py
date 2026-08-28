import io
import json
import os
from unittest import mock
import unittest

from goblin_guard.evidence_cli import main


class EvidenceCliTests(unittest.TestCase):
    def test_synthetic_mode_is_explicit_and_orderless(self):
        output = io.StringIO()
        with mock.patch("sys.stdout", output):
            self.assertEqual(main(["AAPL", "--synthetic"]), 0)
        payload = json.loads(output.getvalue())
        self.assertEqual(payload["mode"], "synthetic")
        self.assertEqual(payload["order_submission"], "disabled")
        self.assertEqual(payload["evidence"]["source"], "synthetic_demo_fixture")

    def test_live_mode_without_credentials_fails_closed(self):
        error = io.StringIO()
        with mock.patch.dict(os.environ, {}, clear=True), mock.patch("sys.stderr", error):
            self.assertEqual(main(["AAPL"]), 2)
        self.assertIn("Live market data is disabled", error.getvalue())


if __name__ == "__main__":
    unittest.main()
