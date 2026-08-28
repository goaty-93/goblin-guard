from datetime import datetime, timezone
from decimal import Decimal
import json
import os
from pathlib import Path
import tempfile
import unittest

from goblin_guard import AuditEvent, JsonlAuditLog


class AuditTests(unittest.TestCase):
    def test_events_append_as_independent_json_lines_with_private_mode(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "audit" / "decisions.jsonl"
            log = JsonlAuditLog(path)
            log.append(AuditEvent("corr-1","proposal",datetime(2026,8,28,15,0,tzinfo=timezone.utc),{"notional":Decimal("250")}))
            log.append(AuditEvent("corr-1","verdict",datetime(2026,8,28,15,0,1,tzinfo=timezone.utc),{"status":"approved"}))
            lines = path.read_text().splitlines()
            self.assertEqual(len(lines), 2)
            self.assertEqual(json.loads(lines[0])["details"]["notional"], "250")
            self.assertEqual(json.loads(lines[1])["event_type"], "verdict")
            self.assertEqual(os.stat(path).st_mode & 0o777, 0o600)


if __name__ == "__main__": unittest.main()
