# Goblin Guard

Goblin Guard is an explainable, paper-trading-only agent for the Alpaca AI Trading Agents Hackathon. AI may propose a trade; deterministic code independently validates evidence and approves, resizes, or rejects the proposal.

The Day 1 demo is a synthetic replay. It has no broker credentials and cannot submit orders.

## Run the console

```bash
npm install
npm run dev
```

## Run the deterministic governor tests

```bash
PYTHONPATH=backend python3 -m unittest discover -s backend/tests -v
```

## Build an evidence packet

The committed fixture exercises the same validation and normalization path without credentials:

```bash
PYTHONPATH=backend python3 -m goblin_guard.evidence_cli AAPL --synthetic
```

For live, read-only Alpaca IEX bars, place dedicated paper-account values in an ignored `.env`, export them into your shell, then omit `--synthetic`. Credentials are sent only as request headers and are never included in evidence, logs, URLs, or browser code.

## Safety boundary

`evidence -> AI proposal -> schema validation -> deterministic risk governor -> paper-order adapter -> audit trace`

The model never receives broker order tools or broker credentials. The future paper-order adapter remains disconnected until its endpoint, idempotency, reconciliation, and kill-switch gates are tested.
