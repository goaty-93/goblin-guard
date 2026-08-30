from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
import json
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from .workflow import WorkflowResult
from .audit import AuditEvent, JsonlAuditLog


class PaperOrderError(RuntimeError):
    """A safe, actionable paper-order boundary failure."""


class OrderOutcomeUnknown(PaperOrderError):
    """Submission may have reached Alpaca, so callers must never retry blindly."""


@dataclass(frozen=True)
class AlpacaPaperOrderConfig:
    api_key: str
    api_secret: str
    submission_enabled: bool = False
    base_url: str = "https://paper-api.alpaca.markets"
    timeout_seconds: float = 8.0

    def __post_init__(self) -> None:
        if not self.api_key or not self.api_secret:
            raise ValueError("Alpaca paper credentials are required")
        if self.base_url.rstrip("/") != "https://paper-api.alpaca.markets":
            raise ValueError("paper-order base URL must be https://paper-api.alpaca.markets")


@dataclass(frozen=True)
class PaperOrderReceipt:
    order_id: str
    client_order_id: str
    symbol: str
    side: str
    notional: Decimal
    status: str
    reconciled: bool
    request_id: str | None = None


@dataclass(frozen=True)
class PaperAccountSnapshot:
    status: str
    trading_blocked: bool
    equity: Decimal
    last_equity: Decimal
    buying_power: Decimal

    @property
    def daily_return_pct(self) -> Decimal:
        if self.last_equity <= 0:
            raise PaperOrderError("Alpaca paper account last equity is invalid")
        return ((self.equity - self.last_equity) / self.last_equity) * Decimal(100)


def client_order_id_for(result: WorkflowResult) -> str:
    return f"{result.correlation_id}-v1"


class AlpacaPaperOrderAdapter:
    def __init__(self, config: AlpacaPaperOrderConfig, opener: Callable[..., Any] = urlopen, audit_log: JsonlAuditLog | None = None):
        self.config = config
        self._opener = opener
        self._audit_log = audit_log

    def _audit(self, result: WorkflowResult, event_type: str, details: dict[str, Any]) -> None:
        if self._audit_log is not None:
            self._audit_log.append(AuditEvent(result.correlation_id, event_type, datetime.now(timezone.utc), details))

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "APCA-API-KEY-ID": self.config.api_key,
            "APCA-API-SECRET-KEY": self.config.api_secret,
            "Accept": "application/json",
        }

    def _load(self, request: Request) -> tuple[Any, str | None]:
        with self._opener(request, timeout=self.config.timeout_seconds) as response:
            request_id = response.headers.get("X-Request-ID") if getattr(response, "headers", None) else None
            return json.load(response), request_id

    def _verify_account(self) -> None:
        request = Request(f"{self.config.base_url}/v2/account", headers=self._headers, method="GET")
        try:
            payload, _ = self._load(request)
        except HTTPError as exc:
            raise PaperOrderError(f"Alpaca paper account check returned HTTP {exc.code}") from None
        except (URLError, TimeoutError, json.JSONDecodeError):
            raise PaperOrderError("Alpaca paper account check is unavailable") from None
        if not isinstance(payload, dict) or type(payload.get("trading_blocked")) is not bool:
            raise PaperOrderError("Alpaca paper account returned an invalid response")
        if payload["trading_blocked"]:
            raise PaperOrderError("Alpaca paper account is blocked from trading")
        if payload.get("status") not in {"ACTIVE", "PAPER_ONLY"}:
            raise PaperOrderError("Alpaca paper account is not active")

    def account_snapshot(self) -> PaperAccountSnapshot:
        request = Request(f"{self.config.base_url}/v2/account", headers=self._headers, method="GET")
        try:
            payload, _ = self._load(request)
        except HTTPError as exc:
            raise PaperOrderError(f"Alpaca paper account check returned HTTP {exc.code}") from None
        except (URLError, TimeoutError, json.JSONDecodeError):
            raise PaperOrderError("Alpaca paper account check is unavailable") from None
        if not isinstance(payload, dict) or type(payload.get("trading_blocked")) is not bool:
            raise PaperOrderError("Alpaca paper account returned an invalid response")
        try:
            snapshot = PaperAccountSnapshot(
                str(payload["status"]), payload["trading_blocked"],
                Decimal(str(payload["equity"])), Decimal(str(payload["last_equity"])),
                Decimal(str(payload["buying_power"])),
            )
        except (KeyError, ValueError, ArithmeticError):
            raise PaperOrderError("Alpaca paper account returned an invalid response") from None
        if snapshot.status not in {"ACTIVE", "PAPER_ONLY"} or snapshot.trading_blocked:
            raise PaperOrderError("Alpaca paper account is not active for trading")
        if min(snapshot.equity, snapshot.last_equity, snapshot.buying_power) < 0:
            raise PaperOrderError("Alpaca paper account returned an invalid response")
        return snapshot

    def _verify_asset(self, symbol: str) -> None:
        request = Request(f"{self.config.base_url}/v2/assets/{quote(symbol, safe='')}", headers=self._headers, method="GET")
        try:
            payload, _ = self._load(request)
        except HTTPError as exc:
            raise PaperOrderError(f"Alpaca paper asset check returned HTTP {exc.code}") from None
        except (URLError, TimeoutError, json.JSONDecodeError):
            raise PaperOrderError("Alpaca paper asset check is unavailable") from None
        if not isinstance(payload, dict) or payload.get("symbol") != symbol:
            raise PaperOrderError("Alpaca paper asset returned an invalid response")
        if payload.get("status") != "active" or payload.get("tradable") is not True or payload.get("fractionable") is not True:
            raise PaperOrderError(f"{symbol} is not active, tradable, and fractionable")

    def _reconcile(self, client_order_id: str) -> PaperOrderReceipt | None:
        query = urlencode({"client_order_id": client_order_id})
        request = Request(f"{self.config.base_url}/v2/orders:by_client_order_id?{query}", headers=self._headers, method="GET")
        try:
            payload, request_id = self._load(request)
        except HTTPError as exc:
            if exc.code == 404:
                return None
            raise PaperOrderError(f"Alpaca paper reconciliation returned HTTP {exc.code}") from None
        except (URLError, TimeoutError, json.JSONDecodeError):
            raise PaperOrderError("Alpaca paper reconciliation is unavailable") from None
        return self._receipt(payload, client_order_id, reconciled=True, request_id=request_id)

    @staticmethod
    def _receipt(payload: Any, expected_client_order_id: str, *, reconciled: bool, request_id: str | None) -> PaperOrderReceipt:
        if not isinstance(payload, dict):
            raise PaperOrderError("Alpaca paper order returned an invalid response")
        required = {"id", "client_order_id", "symbol", "side", "notional", "status"}
        if required - payload.keys() or payload.get("client_order_id") != expected_client_order_id:
            raise PaperOrderError("Alpaca paper order returned an invalid response")
        try:
            notional = Decimal(str(payload["notional"]))
        except Exception:
            raise PaperOrderError("Alpaca paper order returned an invalid response") from None
        if notional <= 0:
            raise PaperOrderError("Alpaca paper order returned an invalid response")
        return PaperOrderReceipt(str(payload["id"]), expected_client_order_id, str(payload["symbol"]), str(payload["side"]), notional, str(payload["status"]), reconciled, request_id)

    def submit_approved(self, result: WorkflowResult) -> PaperOrderReceipt:
        if not self.config.submission_enabled:
            raise PaperOrderError("paper-order submission is disabled")
        if result.order_submission != "disabled":
            raise PaperOrderError("unexpected workflow order state")
        if result.decision.rejected or result.decision.status not in {"approved", "resized"}:
            raise PaperOrderError("only an approved governor verdict may reach the adapter")
        if result.proposal.action not in {"buy", "sell"} or result.decision.approved_notional <= 0:
            raise PaperOrderError("approved order intent is invalid")

        client_order_id = client_order_id_for(result)
        self._verify_account()
        self._verify_asset(result.proposal.symbol)
        existing = self._reconcile(client_order_id)
        if existing is not None:
            self._audit(result, "paper_order_reconciled", {"order_id":existing.order_id,"client_order_id":existing.client_order_id,"symbol":existing.symbol,"side":existing.side,"notional":existing.notional,"status":existing.status,"request_id":existing.request_id})
            return existing

        body = json.dumps({
            "symbol": result.proposal.symbol,
            "notional": str(result.decision.approved_notional),
            "side": result.proposal.action,
            "type": "market",
            "time_in_force": "day",
            "extended_hours": False,
            "client_order_id": client_order_id,
        }, separators=(",", ":")).encode()
        headers = {**self._headers, "Content-Type": "application/json"}
        request = Request(f"{self.config.base_url}/v2/orders", data=body, headers=headers, method="POST")
        try:
            payload, request_id = self._load(request)
            receipt = self._receipt(payload, client_order_id, reconciled=False, request_id=request_id)
            self._audit(result, "paper_order_submitted", {"order_id":receipt.order_id,"client_order_id":receipt.client_order_id,"symbol":receipt.symbol,"side":receipt.side,"notional":receipt.notional,"status":receipt.status,"request_id":receipt.request_id})
            return receipt
        except HTTPError as exc:
            if 400 <= exc.code < 500:
                raise PaperOrderError(f"Alpaca paper order returned HTTP {exc.code}") from None
        except (URLError, TimeoutError, json.JSONDecodeError):
            pass

        try:
            reconciled = self._reconcile(client_order_id)
        except PaperOrderError:
            reconciled = None
        if reconciled is not None:
            self._audit(result, "paper_order_reconciled", {"order_id":reconciled.order_id,"client_order_id":reconciled.client_order_id,"symbol":reconciled.symbol,"side":reconciled.side,"notional":reconciled.notional,"status":reconciled.status,"request_id":reconciled.request_id})
            return reconciled
        self._audit(result, "paper_order_outcome_unknown", {"client_order_id":client_order_id,"symbol":result.proposal.symbol,"side":result.proposal.action,"notional":result.decision.approved_notional,"retry_permitted":False})
        raise OrderOutcomeUnknown("paper-order outcome is unknown; reconcile before any further action")
