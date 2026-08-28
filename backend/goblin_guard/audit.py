from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from decimal import Decimal
import json
import os
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class AuditEvent:
    correlation_id: str
    event_type: str
    occurred_at: datetime
    details: dict[str, Any]

    def to_json(self) -> str:
        def encode(value: Any):
            if isinstance(value, datetime): return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
            if isinstance(value, Decimal): return str(value)
            raise TypeError(f"unsupported audit value: {type(value).__name__}")
        return json.dumps(asdict(self), sort_keys=True, separators=(",", ":"), default=encode)


class JsonlAuditLog:
    """Process-safe append-only JSONL writer; callers control retention."""

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def append(self, event: AuditEvent) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        flags = os.O_APPEND | os.O_CREAT | os.O_WRONLY
        descriptor = os.open(self.path, flags, 0o600)
        try:
            os.write(descriptor, (event.to_json() + "\n").encode("utf-8"))
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
